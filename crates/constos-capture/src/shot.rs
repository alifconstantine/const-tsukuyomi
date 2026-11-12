use crate::{checked, epoch, lock, media_dir, notify, runtime, Result};
use std::env;
use std::fs::{self, File};
use std::io::{self, Read};
use std::path::Path;
use std::process::{Command, Stdio};
use tempfile::Builder;

// Hold the Dux screenshot handshake through selection and capture.
struct HidePopouts;

impl HidePopouts {
    fn begin() -> Self {
        dms("begin");
        Self
    }
}

impl Drop for HidePopouts {
    fn drop(&mut self) {
        dms("end");
    }
}

fn dms(action: &str) {
    let _ = Command::new("timeout")
        .args(["1", "dms", "ipc", "call", "screenshot", action])
        .output();
}

pub fn grab(mode: &str, quick: bool) -> Result<bool> {
    if env::var_os("WAYLAND_DISPLAY").is_none() {
        return Err("The Wayland session is unavailable.".into());
    }
    let Some(_lock) = lock("shot.lock")? else {
        return Ok(quick);
    };
    let runtime = runtime()?;
    let file = Builder::new().suffix(".png").tempfile_in(&runtime)?;
    {
        let _hidden = HidePopouts::begin();
        let mut grim = Command::new("grim");
        if mode == "region" {
            let selection = Command::new("slurp").output()?;
            let detail = String::from_utf8_lossy(&selection.stderr);
            if selection.status.code() == Some(1)
                && matches!(detail.trim(), "" | "selection cancelled")
            {
                return Ok(quick);
            }
            let geometry = String::from_utf8(checked(selection, "Area selection failed")?.stdout)?;
            if geometry.trim().is_empty() {
                return Ok(quick);
            }
            grim.args(["-g", geometry.trim()]);
        }
        checked(grim.arg(file.path()).output()?, "Screenshot capture failed")?;
        check_png(file.path())?;
    }

    if quick {
        copy(file.path())?;
        notify(
            "Screenshot copied",
            "The image is available on the clipboard.",
        );
    } else {
        file.persist(runtime.join("preview.png"))?;
    }
    Ok(true)
}

fn check_png(path: &Path) -> Result<()> {
    let mut header = [0; 24];
    File::open(path)?.read_exact(&mut header)?;
    if &header[..8] != b"\x89PNG\r\n\x1a\n" || &header[12..16] != b"IHDR" {
        return Err("The screenshot backend did not produce a PNG.".into());
    }
    Ok(())
}

fn copy(path: &Path) -> Result<()> {
    let input = File::open(path)?;
    checked(
        Command::new("wl-copy")
            .args(["--type", "image/png"])
            .stdin(input)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .output()?,
        "Clipboard copy failed",
    )?;
    Ok(())
}

pub fn copy_preview() -> Result<()> {
    copy(&runtime()?.join("preview.png"))
}

pub fn save_preview() -> Result<()> {
    let dir = media_dir("PICTURES", "Pictures", "Screenshots")?;
    let mut file = Builder::new().prefix(".Screenshot-").tempfile_in(dir)?;
    io::copy(
        &mut File::open(runtime()?.join("preview.png"))?,
        file.as_file_mut(),
    )?;
    let id = file.path().file_name().unwrap().to_string_lossy();
    let path =
        file.path()
            .with_file_name(format!("{}-{}.png", id.trim_start_matches('.'), epoch()));
    file.persist_noclobber(&path)?;
    println!("{}", path.display());
    Ok(())
}

pub fn edit_preview() -> Result<bool> {
    let runtime = runtime()?;
    let preview = runtime.join("preview.png");
    check_png(&preview)?;
    let file = Builder::new().suffix(".png").tempfile_in(&runtime)?;
    checked(
        Command::new("satty")
            .arg("--filename")
            .arg(&preview)
            .arg("--output-filename")
            .arg(file.path())
            .args([
                "--actions-on-enter",
                "save-to-file,exit",
                "--actions-on-escape",
                "exit",
            ])
            .output()?,
        "Could not open the screenshot editor",
    )?;
    if fs::metadata(file.path())?.len() == 0 {
        return Ok(false);
    }
    check_png(file.path())?;
    file.persist(preview)?;
    Ok(true)
}

pub fn discard() -> Result<()> {
    if let Some(_lock) = lock("shot.lock")? {
        dms("end");
    }
    match fs::remove_file(runtime()?.join("preview.png")) {
        Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(()),
        result => Ok(result?),
    }
}
