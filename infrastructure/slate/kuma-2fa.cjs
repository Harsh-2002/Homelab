const fs = require("node:fs");
const { io } = require("/opt/uptime-kuma/node_modules/socket.io-client");

const action = process.argv[2];
const username = process.argv[3];
const [password, token] = fs.readFileSync(0, "utf8").trimEnd().split(/\r?\n/);
if (!["prepare", "save", "verify"].includes(action) || !username || !password) process.exit(2);

const socket = io("http://127.0.0.1:3001", {
    transports: ["websocket"],
    reconnection: false,
    timeout: 20000,
});
const timer = setTimeout(() => finish("request timed out"), 30000);

function finish(error, output) {
    clearTimeout(timer);
    socket.close();
    if (error) console.error(error);
    else if (output) process.stdout.write(output);
    process.exit(error ? 1 : 0);
}

socket.on("connect_error", (error) => finish(error.message));
socket.on("connect", () => {
    socket.emit("login", { username, password, token }, (login) => {
        if (!login.ok) return finish(login.msg || "login failed");
        if (action === "verify") return finish(null, "login verified\n");
        socket.emit(action === "prepare" ? "prepare2FA" : "save2FA", password, (result) =>
            finish(result.ok ? null : result.msg || "2FA setup failed", action === "prepare" ? result.uri : "2FA enabled\n")
        );
    });
});
