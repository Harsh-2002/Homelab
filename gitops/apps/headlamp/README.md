# Headlamp

Headlamp is the operational Kubernetes UI. Argo CD remains the authoritative deployment controller; use Headlamp for inspection, logs, events, troubleshooting, and deliberate administrative operations.

## Access

- URL: `https://headlamp.l3b.cc.cd`
- Cilium LoadBalancer: `10.1.1.173:80`
- Network access: private Caddy policy
- Authentication: Kubernetes service-account token

Retrieve the permanent administrative login token on `dev`:

```bash
kubectl -n headlamp get secret headlamp-admin-token \
  -o go-template='{{.data.token | base64decode}}{{"\n"}}'
```

Paste the token into the Headlamp login page. It remains valid until the Secret is deleted or rotated. Do not save it in Git, Notion, shell scripts, or Caddy configuration. The `headlamp-admin` identity has `cluster-admin`; store the token in a password manager and create narrower RBAC identities later for non-administrative users.

Rotate the credential by deleting the Secret and letting Argo CD recreate it:

```bash
kubectl -n headlamp delete secret headlamp-admin-token
kubectl -n argocd annotate application headlamp \
  argocd.argoproj.io/refresh=hard --overwrite
```

## Operations

```bash
kubectl -n headlamp get deployment,pods,service,poddisruptionbudget
kubectl auth can-i --as=system:serviceaccount:headlamp:headlamp-admin '*' '*'
```

Headlamp runs two stateless replicas distributed across nodes when possible. It has no persistent volume. Authentik/OIDC is the planned replacement for the permanent administrator token.
