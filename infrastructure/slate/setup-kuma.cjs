const fs = require("node:fs");
const { io } = require("/opt/uptime-kuma/node_modules/socket.io-client");

const username = process.argv[2];
const password = fs.readFileSync(0, "utf8").trimEnd();
if (!username || !password) process.exit(2);

const socket = io("http://127.0.0.1:3001", {
    transports: ["websocket"],
    reconnection: false,
    timeout: 20000,
});
const timer = setTimeout(() => finish("setup timed out"), 30000);

function finish(error) {
    clearTimeout(timer);
    socket.close();
    if (error) console.error(error);
    else console.log("Kuma administrator created");
    process.exit(error ? 1 : 0);
}

socket.on("connect_error", (error) => finish(error.message));
socket.on("connect", () => {
    socket.emit("needSetup", (needed) => {
        if (!needed) return finish("Kuma is already initialized");
        socket.emit("setup", username, password, (result) =>
            finish(result.ok ? null : result.msg || "setup failed")
        );
    });
});
