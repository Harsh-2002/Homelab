const fs = require("node:fs");
const { io } = require("/opt/uptime-kuma/node_modules/socket.io-client");

const username = process.argv[2];
const { password, otp, publisherToken } = JSON.parse(fs.readFileSync(0, "utf8"));
if (!username || !password || !otp || !publisherToken) process.exit(2);

const socket = io("http://127.0.0.1:3001", {
    transports: ["websocket"],
    reconnection: false,
    timeout: 20000,
});
let existingMonitors = {};
let existingNotifications = [];
const timer = setTimeout(() => fail("configuration timed out"), 120000);

function fail(message) {
    console.error(message);
    clearTimeout(timer);
    socket.close();
    process.exit(1);
}

function call(event, ...args) {
    return new Promise((resolve, reject) => {
        socket.timeout(30000).emit(event, ...args, (error, result) => {
            if (error) return reject(error);
            if (!result?.ok) return reject(new Error(result?.msg || `${event} failed`));
            resolve(result);
        });
    });
}

function monitor(name, overrides) {
    return {
        type: "http",
        name,
        parent: null,
        active: true,
        method: "GET",
        interval: 60,
        retryInterval: 60,
        maxretries: 2,
        resendInterval: 0,
        maxredirects: 5,
        ignoreTls: false,
        upsideDown: false,
        accepted_statuscodes: ["200-299"],
        kafkaProducerBrokers: [],
        kafkaProducerSaslOptions: { mechanism: "None" },
        rabbitmqNodes: [],
        conditions: [],
        ...overrides,
    };
}

socket.on("monitorList", (list) => { existingMonitors = list || {}; });
socket.on("notificationList", (list) => { existingNotifications = list || []; });
socket.on("connect_error", (error) => fail(error.message));
socket.on("connect", async () => {
    try {
        await call("login", { username, password, token: otp });
        const notification = {
            name: "ntfy infra",
            type: "ntfy",
            isDefault: true,
            ntfyserverurl: "http://127.0.0.1:2586",
            ntfytopic: "infra",
            ntfyAuthenticationMethod: "accessToken",
            ntfyaccesstoken: publisherToken,
            ntfyPriority: 3,
            ntfyPriorityDown: 5,
        };
        let existing = existingNotifications.find((item) => item.name === notification.name);
        let notificationID;
        if (existing) {
            notificationID = existing.id;
        } else {
            await call("testNotification", notification);
            notificationID = (await call("addNotification", notification, null)).id;
            console.log(`Notification configured: ${notification.name}`);
        }

        const notificationIDList = { [notificationID]: true };
        const monitors = [
            monitor("Home public web", { url: "https://store.l3b.cc.cd/" }),
            monitor("Home private proxy", {
                url: "https://dns.l3b.cc.cd/",
                accepted_statuscodes: ["401"],
            }),
            monitor("Home DNS", {
                type: "dns",
                hostname: "l3b.cc.cd",
                dns_resolve_server: "10.1.1.2",
                dns_resolve_type: "A",
                port: 53,
            }),
            ...[10, 20, 30].map((node) => monitor(`Proxmox px${node}`, {
                url: `https://10.1.1.${node}:8006/api2/json/version`,
                accepted_statuscodes: ["401"],
                ignoreTls: true,
            })),
        ];

        const names = new Set(Object.values(existingMonitors).map((item) => item.name));
        for (const item of monitors) {
            if (names.has(item.name)) continue;
            const result = await call("add", { ...item, notificationIDList });
            console.log(`Monitor configured: ${item.name} (${result.monitorID})`);
        }
        clearTimeout(timer);
        socket.close();
        process.exit(0);
    } catch (error) {
        fail(error.message);
    }
});
