# Headlamp

Headlamp is the operational Kubernetes UI. Argo CD remains the authoritative deployment controller; use Headlamp for inspection, logs, events, troubleshooting, and deliberate administrative operations.

## Access

- URL: `https://headlamp.l3b.cc.cd`
- Cilium LoadBalancer: `10.1.1.173:80`
- Network access: private Caddy policy
- Authentication: Kubernetes service-account token

Generate a short-lived administrative login token on `dev` when needed:

```bash
kubectl -n headlamp create token headlamp-admin --duration=24h
```

Paste the token into the Headlamp login page. Do not save the token in Git, Notion, shell scripts, or Caddy configuration. The `headlamp-admin` identity has `cluster-admin`; create narrower RBAC identities later for non-administrative users.

## Operations

```bash
kubectl -n headlamp get deployment,pods,service,poddisruptionbudget
kubectl auth can-i --as=system:serviceaccount:headlamp:headlamp-admin '*' '*'
```

Headlamp runs two stateless replicas distributed across nodes when possible. It has no persistent volume. Authentik/OIDC is the planned replacement for token login.
