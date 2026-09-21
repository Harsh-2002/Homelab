# Homepage

Homepage is the stateless, Git-managed portal served at `https://l3b.cc.cd`.

- Argo CD deploys this Helm chart into the `homepage` namespace.
- `homepage-config` is the source of truth for the visible page: `services.yaml`, `settings.yaml`, `widgets.yaml`, and `kubernetes.yaml` are ConfigMap entries rendered from Git.
- It uses a read-only Kubernetes service account solely for cluster and resource widgets.
- Cilium advertises `10.1.1.174:80`; Caddy terminates TLS, applies private LAN/Tailscale access control, and uses Tinyauth/Pocket ID for authentication.
- There are intentionally no API credentials or other secrets in this initial dashboard. Add a narrowly scoped secret only when a useful service widget requires one.

Validate after an Argo sync:

```bash
kubectl --context k8s -n homepage get deploy,pods,svc
curl -I https://l3b.cc.cd
```
