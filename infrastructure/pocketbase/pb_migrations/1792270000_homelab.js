migrate((app) => {
  const email = $os.getenv("PB_ADMIN_EMAIL");
  const password = $os.getenv("PB_ADMIN_PASSWORD");
  if (!email || password.length < 32) {
    throw new Error("Missing protected PocketBase bootstrap credentials");
  }
  const record = new Record(app.findCollectionByNameOrId("_superusers"));
  record.set("email", email);
  record.set("password", password);
  app.save(record);

  const settings = app.settings();
  settings.meta.appName = "Homelab PocketBase";
  settings.meta.appURL = "https://pocketbase.l3b.cc.cd";
  settings.logs.maxDays = 7;
  settings.rateLimits.enabled = true;
  settings.trustedProxy.headers = ["X-Forwarded-For"];
  settings.trustedProxy.useLeftmostIP = false;
  settings.backups.cron = "0 22 * * *";
  settings.backups.cronMaxKeep = 3;
  app.save(settings);
});
