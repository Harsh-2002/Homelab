# GitOps

Argo CD manages the primary cluster from the `main` branch of this repository.

## Layout

- `bootstrap/argocd/` — pinned Argo CD umbrella chart and cluster values.
- `bootstrap/root.yaml` — one-time root Application bootstrap.
- `clusters/platform/applications/` — child Application definitions.
- `apps/` — workload manifests managed by those Applications.

Headlamp is pinned under `apps/headlamp/` and provides the operational Kubernetes UI. Argo CD remains authoritative for declarative changes.

Longhorn is pinned under `apps/longhorn/`. It uses dedicated Talos mounts at `/var/mnt/longhorn`, the V1 data engine, and two replicas. The Longhorn Application intentionally disables automatic pruning because Argo CD cannot run Longhorn's required pre-delete uninstall workflow.

See [`apps/longhorn/README.md`](apps/longhorn/README.md) for capacity, validation results, maintenance, and recovery notes.

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

The `platform` root Application discovers the child Applications. The `argocd` child then adopts and manages the bootstrap Helm release from Git.

## Access

- URL: `https://argocd.l3b.cc.cd`
- Internal service: `10.1.1.171:80`
- TLS and private network access control: Caddy on the proxy node.
- Local DNS: AdGuard rewrites `argocd.l3b.cc.cd` to the Caddy proxy.

For CLI access through Caddy, use gRPC-Web:

```bash
argocd login argocd.l3b.cc.cd --grpc-web
```

## Authentication

The permanent local administrator account is `iam-anuragvishwakarma`. It has the `login` capability and an explicit `role:admin` RBAC assignment. The built-in `admin` account is disabled after the replacement account was verified through Caddy.

An email address cannot be used directly as an Argo CD local username: `@` is invalid in a ConfigMap data key, and dots are parsed as configuration separators. The hyphenated username is intentional.

The one-time password is stored only on `dev` in a mode-600 file until the owner completes the interactive rotation:

```bash
argocd account update-password \
  --current-password "$(tr -d '\n' < ~/.config/argocd/iam-anuragvishwakarma.initial-password)" \
  --grpc-web \
  --prompts-enabled
```

After changing the password, verify a fresh login and securely remove the one-time credential:

```bash
argocd logout argocd.l3b.cc.cd
argocd login argocd.l3b.cc.cd \
  --username iam-anuragvishwakarma \
  --grpc-web \
  --prompts-enabled
shred --remove ~/.config/argocd/iam-anuragvishwakarma.initial-password
```

Passwords and password hashes must not be committed to Git or copied into documentation.

## Change workflow

1. Modify manifests or pinned values in Git.
2. Run `helm lint gitops/bootstrap/argocd` when changing Argo CD.
3. Review the Git diff and ensure it contains no plaintext secret material.
4. Commit and push to `main`.
5. Confirm the affected Application is `Synced` and `Healthy`.

Do not commit plaintext secrets. SOPS with age must be introduced before the first secret-bearing workload is added.

## Longhorn operations

Validate the storage layer before assigning real workloads:

```bash
kubectl --context k8s -n longhorn-system get pods
kubectl --context k8s -n longhorn-system get nodes.longhorn.io
kubectl --context k8s get storageclass longhorn
```

Do not delete the Argo CD Application as an uninstall method. Follow Longhorn's uninstall job procedure after all Longhorn-backed workloads and volumes have been removed.
