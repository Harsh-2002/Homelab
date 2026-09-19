# GitOps

Argo CD manages the homelab cluster from the `main` branch of this repository.

## Layout

- `bootstrap/argocd/` — pinned Argo CD umbrella chart and homelab values.
- `bootstrap/root.yaml` — one-time root Application bootstrap.
- `clusters/homelab/applications/` — child Application definitions.
- `apps/` — workload manifests managed by those Applications.

## Bootstrap or recovery

```bash
helm dependency update gitops/bootstrap/argocd
helm upgrade --install argocd gitops/bootstrap/argocd \
  --namespace argocd \
  --create-namespace \
  --atomic \
  --timeout 10m

kubectl --context k8s apply --server-side \
  --filename gitops/bootstrap/root.yaml
```

The root Application discovers the child Applications. The `argocd` child then adopts and manages the bootstrap Helm release from Git.

## Access

- URL: `https://argocd.l3b.cc.cd`
- Internal service: `10.1.1.171:80`
- TLS and private network access control: Caddy on the proxy node.
- Local DNS: AdGuard rewrites `argocd.l3b.cc.cd` to the Caddy proxy.

For CLI access through Caddy, use gRPC-Web:

```bash
argocd login argocd.l3b.cc.cd --grpc-web
```

## Change workflow

1. Modify manifests or pinned values in Git.
2. Run `helm lint gitops/bootstrap/argocd` when changing Argo CD.
3. Review the Git diff and ensure it contains no plaintext secret material.
4. Commit and push to `main`.
5. Confirm the affected Application is `Synced` and `Healthy`.

Do not commit plaintext secrets. SOPS with age must be introduced before the first secret-bearing workload is added.
