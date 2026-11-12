mod audio;
mod shot;

use std::env;
use std::error::Error;
use std::fs::{self, DirBuilder, File, OpenOptions};
use std::io;
use std::os::unix::fs::{DirBuilderExt, OpenOptionsExt};
use std::path::PathBuf;
use std::process::{Command, ExitCode, Output};
use std::time::{SystemTime, UNIX_EPOCH};

type Result<T> = std::result::Result<T, Box<dyn Error>>;

fn main() -> ExitCode {
    let args: Vec<_> = env::args().skip(1).collect();
    let args: Vec<_> = args.iter().map(String::as_str).collect();
    match run(&args) {
        Ok(true) => ExitCode::SUCCESS,
        Ok(false) => ExitCode::from(2),
        Err(error) => {
            eprintln!("{error}");
            if matches!(args.first(), Some(&"quick")) {
                notify("Screenshot failed", &error.to_string());
            }
            ExitCode::FAILURE
        }
    }
}

fn run(args: &[&str]) -> Result<bool> {
    match args {
        ["quick"] => shot::grab("region", true),
        [action @ ("grab" | "quick"), mode @ ("region" | "screen")] => {
            shot::grab(mode, *action == "quick")
        }
        ["copy"] => shot::copy_preview().map(|()| true),
        ["save"] => shot::save_preview().map(|()| true),
        ["edit"] => shot::edit_preview(),
        ["discard"] => shot::discard().map(|()| true),
        ["sources"] => {
            println!("{}", serde_json::to_string(&audio::sources()?)?);
            Ok(true)
        }
        ["record", serial] => audio::record(serial.parse()?).map(|()| true),
        ["status"] => audio::print_status().map(|()| true),
        ["stop"] => audio::stop().map(|()| true),
        _ => Err("Usage: constos-capture quick|grab [region|screen], copy, save, edit, discard, sources, record SERIAL, status, or stop".into()),
    }
}

fn runtime() -> Result<PathBuf> {
    let root = PathBuf::from(
        env::var_os("XDG_RUNTIME_DIR").ok_or("The session runtime directory is unavailable.")?,
    );
    if !root.is_absolute() || !root.is_dir() {
        return Err("The session runtime directory is unavailable.".into());
    }
    let path = root.join("constos-capture");
    match DirBuilder::new().mode(0o700).create(&path) {
        Ok(()) => {}
        Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {}
        Err(error) => return Err(error.into()),
    }
    if !path.symlink_metadata()?.is_dir() {
        return Err("The capture runtime path is invalid.".into());
    }
    Ok(path)
}

fn lock(name: &str) -> Result<Option<File>> {
    let file = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .mode(0o600)
        .open(runtime()?.join(name))?;
    match file.try_lock() {
        Ok(()) => Ok(Some(file)),
        Err(std::fs::TryLockError::WouldBlock) => Ok(None),
        Err(std::fs::TryLockError::Error(error)) => Err(error.into()),
    }
}

fn checked(output: Output, label: &str) -> Result<Output> {
    if output.status.success() {
        return Ok(output);
    }
    let detail = String::from_utf8_lossy(&output.stderr);
    Err(format!(
        "{label}: {}",
        detail.lines().last().unwrap_or("command failed")
    )
    .into())
}

fn media_dir(kind: &str, fallback: &str, folder: &str) -> Result<PathBuf> {
    let home = PathBuf::from(env::var_os("HOME").ok_or("The home directory is unavailable.")?);
    let output = checked(
        Command::new("xdg-user-dir").arg(kind).output()?,
        "Could not locate your media folder",
    )?;
    let configured = PathBuf::from(String::from_utf8(output.stdout)?.trim_end_matches('\n'));
    let base = if configured.is_absolute() && configured != home {
        configured
    } else {
        home.join(fallback)
    };
    let path = base.join(folder);
    fs::create_dir_all(&path)?;
    Ok(path)
}

fn epoch() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

fn notify(title: &str, message: &str) {
    let _ = Command::new("notify-send")
        .args(["--app-name=ConstOS Capture", "--", title, message])
        .status();
}
