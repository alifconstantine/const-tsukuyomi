use crate::{checked, epoch, lock, media_dir, notify, runtime, Result};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::fs::File;
use std::io::{self, BufWriter, Read};
use std::os::fd::AsRawFd;
use std::process::{Child, Command, Stdio};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::thread;
use std::time::{Duration, Instant};
use tempfile::{Builder, NamedTempFile};
use zbus::blocking::{Connection, Proxy};
use zbus::zvariant::OwnedObjectPath;

#[derive(Serialize)]
pub struct Source {
    serial: u64,
    kind: &'static str,
    label: String,
}

pub fn sources() -> Result<Vec<Source>> {
    let output = checked(
        Command::new("pw-dump").output()?,
        "Could not read PipeWire sources",
    )?;
    let objects: Vec<Value> = serde_json::from_slice(&output.stdout)?;
    Ok(objects
        .iter()
        .filter_map(|object| {
            let props = object.get("info")?.get("props")?;
            let kind = match props.get("media.class")?.as_str()? {
                "Audio/Source" => "Microphone",
                "Audio/Sink" => "System audio",
                _ => return None,
            };
            let label = props
                .get("node.description")
                .or_else(|| props.get("node.nick"))
                .or_else(|| props.get("node.name"))?
                .as_str()?
                .to_owned();
            Some(Source {
                serial: props.get("object.serial")?.as_u64()?,
                kind,
                label,
            })
        })
        .collect())
}

#[derive(Default, Serialize, Deserialize)]
struct Status {
    phase: String,
    source: String,
    started: u64,
    path: String,
    message: String,
}

fn write_status(status: &Status) -> Result<()> {
    let dir = runtime()?;
    let mut file = NamedTempFile::new_in(&dir)?;
    serde_json::to_writer(file.as_file_mut(), status)?;
    file.persist(dir.join("audio.json"))?;
    Ok(())
}

pub fn print_status() -> Result<()> {
    let mut status: Status = match File::open(runtime()?.join("audio.json")) {
        Ok(file) => serde_json::from_reader(file)?,
        Err(error) if error.kind() == io::ErrorKind::NotFound => Status::default(),
        Err(error) => return Err(error.into()),
    };
    if matches!(
        status.phase.as_str(),
        "starting" | "recording" | "finalizing"
    ) && lock("audio.lock")?.is_some()
    {
        status.phase = "failed".into();
        status.message = "The recorder stopped unexpectedly.".into();
    }
    println!("{}", serde_json::to_string(&status)?);
    Ok(())
}

pub fn stop() -> Result<()> {
    checked(
        Command::new("systemctl")
            .args(["--user", "stop", "constos-audio@*.service"])
            .output()?,
        "Could not stop the recorder",
    )?;
    Ok(())
}

pub fn record(serial: u64) -> Result<()> {
    let Some(_lock) = lock("audio.lock")? else {
        return Err("A recording is already active.".into());
    };
    let mut status = Status {
        phase: "starting".into(),
        ..Status::default()
    };
    write_status(&status)?;
    let result = record_source(serial, &mut status);
    if let Err(error) = &result {
        status.phase = "failed".into();
        status.message = error.to_string();
        write_status(&status)?;
        notify("Audio recording failed", &status.message);
    }
    result
}

fn record_source(serial: u64, status: &mut Status) -> Result<()> {
    let stopped = Arc::new(AtomicBool::new(false));
    signal_hook::flag::register(libc::SIGTERM, stopped.clone())?;
    signal_hook::flag::register(libc::SIGINT, stopped.clone())?;

    let session_id = std::env::var("XDG_SESSION_ID")?;
    let bus = Connection::system()?;
    let manager = Proxy::new(
        &bus,
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager",
    )?;
    let session_path: OwnedObjectPath = manager.call("GetSession", &(session_id.as_str(),))?;
    let session = Proxy::new(
        &bus,
        "org.freedesktop.login1",
        session_path,
        "org.freedesktop.login1.Session",
    )?;
    if session.get_property::<bool>("LockedHint")? {
        return Err("Unlock the session before recording.".into());
    }

    let source = sources()?
        .into_iter()
        .find(|source| source.serial == serial)
        .ok_or("The selected PipeWire source is no longer available.")?;
    status.source = format!("{} · {}", source.kind, source.label);
    let dir = media_dir("MUSIC", "Music", "Recordings")?;
    let (file, partial) = Builder::new()
        .prefix(".ConstOS-audio-")
        .suffix(".wav")
        .tempfile_in(dir)?
        .into_parts();
    status.path = partial.to_string_lossy().into_owned();
    write_status(status)?;
    let mut wave = hound::WavWriter::new(
        BufWriter::new(file),
        hound::WavSpec {
            channels: 2,
            sample_rate: 48_000,
            bits_per_sample: 16,
            sample_format: hound::SampleFormat::Int,
        },
    )?;

    let props = json!({
        "node.dont-fallback": true,
        "node.dont-reconnect": true,
        "node.dont-move": true,
        "stream.capture.sink": source.kind == "System audio",
    });
    let child = Command::new("pw-record")
        .args([
            "--target",
            &serial.to_string(),
            "--properties",
            &props.to_string(),
            "--format",
            "s16",
            "--rate",
            "48000",
            "--channels",
            "2",
            "--raw",
            "-",
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .spawn();
    let outcome = child
        .map_err(Into::into)
        .and_then(|child| capture(Recorder(child), &mut wave, &session, &stopped, status));

    let samples = wave.duration();
    let finalized = wave.finalize();
    if let Err(error) = outcome.and_then(|()| Ok(finalized?)) {
        if samples > 0 {
            partial.keep()?;
        } else {
            status.path.clear();
        }
        return Err(error);
    }
    if samples == 0 {
        status.path.clear();
        return Err("The recording produced no playable audio.".into());
    }
    let name = partial.file_name().unwrap().to_string_lossy();
    let destination = partial.with_file_name(name.trim_start_matches('.'));
    if let Err(error) = partial.persist_noclobber(&destination) {
        error.path.keep()?;
        return Err(error.error.into());
    }
    status.path = destination.to_string_lossy().into_owned();

    status.phase = "completed".into();
    write_status(status)?;
    notify("Audio recording saved", &status.path);
    Ok(())
}

struct Recorder(Child);

impl Drop for Recorder {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}

fn capture(
    mut recorder: Recorder,
    wave: &mut hound::WavWriter<BufWriter<File>>,
    session: &Proxy<'_>,
    stopped: &AtomicBool,
    status: &mut Status,
) -> Result<()> {
    let mut stream = recorder.0.stdout.take().ok_or("Missing PCM output pipe.")?;
    let fd = stream.as_raw_fd();
    // Preserve the pipe flags and keep reads interruptible while waiting for Stop.
    let flags = unsafe { libc::fcntl(fd, libc::F_GETFL) };
    if flags < 0 || unsafe { libc::fcntl(fd, libc::F_SETFL, flags | libc::O_NONBLOCK) } < 0 {
        return Err(io::Error::last_os_error().into());
    }

    let deadline = Instant::now() + Duration::from_secs(6);
    let mut check_lock = Instant::now();
    let mut stop_time = None;
    let mut buffer = [0; 16 * 1024 + 3];
    let mut carry = 0;
    loop {
        let count = match stream.read(&mut buffer[carry..]) {
            Ok(count) => count,
            Err(error) if error.kind() == io::ErrorKind::WouldBlock => 0,
            Err(error) => return Err(error.into()),
        };
        let used = carry + count;
        let frames = used - used % 4;
        for sample in buffer[..frames].chunks_exact(2) {
            wave.write_sample(i16::from_ne_bytes([sample[0], sample[1]]))?;
        }
        buffer.copy_within(frames..used, 0);
        carry = used - frames;

        if count == 0 {
            if let Some(exit) = recorder.0.try_wait()? {
                // pw-cat returns 1 when SIGINT stops a stream before it drains.
                if stop_time.is_some() && (exit.success() || exit.code() == Some(1)) {
                    return Ok(());
                }
                return Err(format!("The audio stream ended ({exit}).").into());
            }
        }
        if let Some(time) = stop_time {
            if Instant::now() >= time {
                return Err("The recorder did not finalize in time.".into());
            }
        } else {
            let locked = if Instant::now() >= check_lock {
                check_lock = Instant::now() + Duration::from_millis(500);
                session.get_property::<bool>("LockedHint")?
            } else {
                false
            };
            // WAV uses a 32-bit chunk length. Leave space for its header and buffered samples.
            if locked || stopped.load(Ordering::Relaxed) || wave.duration() >= 1_070_000_000 {
                // This unreaped child still owns its PID.
                if unsafe { libc::kill(recorder.0.id() as i32, libc::SIGINT) } != 0 {
                    return Err(io::Error::last_os_error().into());
                }
                stop_time = Some(Instant::now() + Duration::from_secs(5));
                status.phase = "finalizing".into();
                write_status(status)?;
            } else if status.phase == "starting" {
                if wave.duration() > 0 {
                    status.phase = "recording".into();
                    status.started = epoch();
                    write_status(status)?;
                } else if Instant::now() >= deadline {
                    return Err("The selected source did not deliver audio.".into());
                }
            }
        }
        if count == 0 {
            thread::sleep(Duration::from_millis(20));
        }
    }
}
