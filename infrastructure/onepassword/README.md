# 1Password homelab secrets

The `Homelab` vault is the authoritative store for application credentials, API tokens, recovery material, and automation secrets. An isolated service account gives the automation agent `read_items` and `write_items` only in this vault. It must not have access to personal vaults, item sharing, or vault creation.

The service-account token is stored only on `dev` at `~/.config/op/service-account-token`, outside Git, with mode `0600`. Do not paste it into chat, commit it, export it globally, or add it to shell startup files.

Bootstrap once:

```bash
cd ~/Homelab
scripts/set-1password-service-token.sh
scripts/op-sa whoami
scripts/op-sa vault get Homelab
```

Repository configuration may contain `op://Homelab/item/field` references. Resolve them only for the process that needs them with `op run`, `op read`, or `op inject`. Never print a resolved value during validation.

The service account is a privileged machine identity. Review its item-usage report, rotate its token periodically, and revoke it immediately if `dev` or an automation session is compromised. Creating a new account is required to change its immutable vault scope or permissions.
