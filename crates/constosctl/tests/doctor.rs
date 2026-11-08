use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::process::{Command, Output};

const DF_WITH_FREE_SPACE: &str = "printf 'Avail\n1073741824\n'";

fn doctor_with_commands(systemctl_script: &str, df_script: &str) -> Output {
    let fixture = tempfile::tempdir().unwrap();
    for (name, script) in [("systemctl", systemctl_script), ("df", df_script)] {
        let path = fixture.path().join(name);
        fs::write(&path, format!("#!/bin/sh\n{script}\n")).unwrap();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o755)).unwrap();
    }
    Command::new(env!("CARGO_BIN_EXE_const"))
        .arg("doctor")
        .env("PATH", fixture.path())
        .output()
        .unwrap()
}

#[test]
fn doctor_distinguishes_systemd_query_errors_from_failed_units() {
    let unavailable = doctor_with_commands("exit 1", DF_WITH_FREE_SPACE);
    let stdout = String::from_utf8(unavailable.stdout).unwrap();
    assert!(stdout.contains("[UNKNOWN] systemd services"), "{stdout}");
    assert_eq!(unavailable.status.code(), Some(1));

    let failed_unit = doctor_with_commands(
        "printf '%s\\n' 'fixture.service loaded failed failed Fixture'",
        DF_WITH_FREE_SPACE,
    );
    let stdout = String::from_utf8(failed_unit.stdout).unwrap();
    assert!(
        stdout.contains("[FAIL] systemd services · Failed units: 1 (fixture.service)"),
        "{stdout}"
    );
    assert_eq!(failed_unit.status.code(), Some(1));

    let healthy = doctor_with_commands("exit 0", DF_WITH_FREE_SPACE);
    let stdout = String::from_utf8(healthy.stdout).unwrap();
    assert!(
        stdout.contains("[PASS] systemd services · No failed units"),
        "{stdout}"
    );
}

#[test]
fn doctor_reports_available_space_on_the_root_filesystem() {
    let output = doctor_with_commands("exit 0", DF_WITH_FREE_SPACE);
    let stdout = String::from_utf8(output.stdout).unwrap();
    assert!(
        stdout.contains("[PASS] Disk space · 1.00 GiB available on /"),
        "{stdout}"
    );

    let full = doctor_with_commands("exit 0", "printf 'Avail\n0\n'");
    let stdout = String::from_utf8(full.stdout).unwrap();
    assert!(
        stdout.contains("[FAIL] Disk space · No space available on /"),
        "{stdout}"
    );
    assert_eq!(full.status.code(), Some(1));
}

#[test]
fn doctor_reports_unavailable_disk_space_as_unknown() {
    for script in [
        "printf 'Avail\n-\n'",
        "printf 'Avail\n1073741824\n'; exit 1",
    ] {
        let output = doctor_with_commands("exit 0", script);
        let stdout = String::from_utf8(output.stdout).unwrap();
        assert!(stdout.contains("[UNKNOWN] Disk space"), "{stdout}");
        assert_eq!(output.status.code(), Some(1));
    }
}
