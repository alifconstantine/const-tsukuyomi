use const_collector::Collector;
use zbus::blocking::{connection::Builder, MessageIterator};

const BUS_NAME: &str = "org.constos.Monitor1";
const OBJECT_PATH: &str = "/org/constos/Monitor1";

struct Monitor(Collector);

#[zbus::interface(name = "org.constos.Monitor1", spawn = false)]
impl Monitor {
    fn get_snapshot(&self) -> zbus::fdo::Result<String> {
        serde_json::to_string(&self.0.snapshot())
            .map_err(|error| zbus::fdo::Error::Failed(error.to_string()))
    }
}

fn main() -> zbus::Result<()> {
    let connection = Builder::session()?
        .serve_at(OBJECT_PATH, Monitor(Collector::default()))?
        .name(BUS_NAME)?
        .build()?;

    // Keep serving until the session bus disconnects or systemd stops the unit.
    for message in MessageIterator::from(&connection) {
        message?;
    }
    Ok(())
}
