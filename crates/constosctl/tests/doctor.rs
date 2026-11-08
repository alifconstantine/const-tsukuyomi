use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::process::{Command, Output};

fn doctor_with_systemctl(script: &str) -> Output {
    let fixture = tempfile::tempdir().unwrap();
    let systemctl = fixture.path().join("systemctl");
    fs::write(&systemctl, format!("#!/bin/sh\n{script}\n")).unwrap();
    fs::set_permissions(&systemctl, fs::Permissions::from_mode(0o755)).unwrap();
    Command::new(env!("CARGO_BIN_EXE_const"))
        .arg("doctor")
        .env("PATH", fixture.path())
        .output()
        .unwrap()
}

#[test]
fn doctor_distinguishes_systemd_query_errors_from_failed_units() {
    let unavailable = doctor_with_systemctl("exit 1");
    let stdout = String::from_utf8(unavailable.stdout).unwrap();
    assert!(stdout.contains("[UNKNOWN] Layanan systemd"), "{stdout}");
    assert_eq!(unavailable.status.code(), Some(1));

    let failed_unit =
        doctor_with_systemctl("printf '%s\\n' 'fixture.service loaded failed failed Fixture'");
    let stdout = String::from_utf8(failed_unit.stdout).unwrap();
    assert!(
        stdout.contains("[FAIL] Layanan systemd · 1 unit gagal (fixture.service)"),
        "{stdout}"
    );
    assert_eq!(failed_unit.status.code(), Some(1));

    let healthy = doctor_with_systemctl("exit 0");
    let stdout = String::from_utf8(healthy.stdout).unwrap();
    assert!(
        stdout.contains("[PASS] Layanan systemd · 0 unit gagal"),
        "{stdout}"
    );
}
