use std::fs;
use std::io::{self, IsTerminal};
use std::os::unix::process::CommandExt;
use std::path::Path;
use std::process::Command;

fn is_installed_constos() -> io::Result<bool> {
    let cmdline = fs::read_to_string("/proc/cmdline")?;
    if cmdline
        .split_whitespace()
        .any(|arg| arg == "boot=archiso" || arg.starts_with("archisobasedir="))
        || Path::new("/run/archiso/bootmnt").try_exists()?
    {
        return Ok(false);
    }
    let release = fs::read_to_string("/etc/os-release")?;
    Ok(release
        .lines()
        .any(|line| matches!(line, "ID=constos" | "ID=\"constos\"" | "ID='constos'")))
}

pub fn run() -> i32 {
    if !io::stdin().is_terminal() {
        eprintln!("Run const update from an interactive terminal to confirm the transaction.");
        return 1;
    }
    match is_installed_constos() {
        Ok(true) => {}
        Ok(false) => {
            eprintln!("const update is available on installed ConstOS systems only.");
            return 1;
        }
        Err(error) => {
            eprintln!("Could not check the system identity ({error}).");
            return 1;
        }
    }

    // Keep the terminal and exit status of sudo/pacman, including cancellations.
    let error = Command::new("/usr/bin/sudo")
        .args(["--", "/usr/bin/pacman", "-Syu"])
        .exec();
    eprintln!("Could not run sudo to start the update ({error}).");
    1
}
