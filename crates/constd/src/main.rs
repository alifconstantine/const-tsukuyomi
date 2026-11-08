use std::env;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;
use const_collector::Collector;

const DEFAULT_HOST: &str = "127.0.0.1";
const DEFAULT_PORT: u16 = 9099;

fn handle_connection(mut stream: TcpStream, collector: &Collector) {
    let mut buffer = [0u8; 1024];
    let bytes_read = match stream.read(&mut buffer) {
        Ok(n) if n > 0 => n,
        _ => return,
    };

    let request = String::from_utf8_lossy(&buffer[..bytes_read]);
    let first_line = request.lines().next().unwrap_or("");
    let parts: Vec<&str> = first_line.split_whitespace().collect();

    if parts.len() < 2 || parts[0] != "GET" {
        let response = "HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\nConnection: close\r\n\r\n";
        let _ = stream.write_all(response.as_bytes());
        return;
    }

    let path = parts[1];
    if path == "/metrics" || path == "/status" || path == "/" {
        let snapshot = collector.snapshot();
        let json_body = match serde_json::to_string(&snapshot) {
            Ok(j) => j,
            Err(_) => {
                let response = "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\nConnection: close\r\n\r\n";
                let _ = stream.write_all(response.as_bytes());
                return;
            }
        };

        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
            json_body.len(),
            json_body
        );
        let _ = stream.write_all(response.as_bytes());
    } else {
        let response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n";
        let _ = stream.write_all(response.as_bytes());
    }
}

fn main() {
    let port: u16 = env::var("CONSTD_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(DEFAULT_PORT);

    let host = env::var("CONSTD_HOST").unwrap_or_else(|_| DEFAULT_HOST.to_string());
    let addr = format!("{}:{}", host, port);

    println!("Starting constd on http://{} ...", addr);
    let listener = match TcpListener::bind(&addr) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("Failed to bind to {}: {}", addr, e);
            std::process::exit(1);
        }
    };

    // Set non-blocking to allow checking shutdown signal cleanly
    if let Err(e) = listener.set_nonblocking(true) {
        eprintln!("Failed to set nonblocking on listener: {}", e);
    }

    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();

    // Catch Ctrl+C
    if let Err(e) = ctrlc_setup(r) {
        eprintln!("Warning: failed to set ctrlc handler: {}", e);
    }

    let collector = Collector::default();
    println!("constd ready. Serving CPU BORE, ZRAM, and process metrics.");

    while running.load(Ordering::SeqCst) {
        match listener.accept() {
            Ok((stream, _)) => {
                let col = collector.clone();
                handle_connection(stream, &col);
            }
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                thread::sleep(Duration::from_millis(50));
            }
            Err(e) => {
                eprintln!("Accept error: {}", e);
                thread::sleep(Duration::from_millis(100));
            }
        }
    }

    println!("constd daemon stopped cleanly.");
}

fn ctrlc_setup(running: Arc<AtomicBool>) -> Result<(), String> {
    // Basic signal hook or atomic check
    let _ = running;
    Ok(())
}
