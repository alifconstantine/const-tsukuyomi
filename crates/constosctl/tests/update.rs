use std::process::Command;

#[test]
fn update_requires_an_interactive_terminal() {
    let output = Command::new(env!("CARGO_BIN_EXE_const"))
        .arg("update")
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(1));
    assert!(String::from_utf8_lossy(&output.stderr).contains("interactive terminal"));
}

#[test]
fn update_rejects_arguments_that_could_change_the_transaction() {
    let output = Command::new(env!("CARGO_BIN_EXE_const"))
        .args(["update", "--noconfirm"])
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&output.stderr).contains("Usage: const update"));
}
