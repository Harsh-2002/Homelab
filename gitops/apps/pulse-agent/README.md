# Pulse Kubernetes collector

The `v6.4.1` DaemonSet reports Kubernetes inventory and metrics to the external Pulse server at `https://pulse.l3b.cc.cd`. It runs without host mounts, Docker sockets, privileged mode, or command execution.

The `pulse-agent-token` Secret is created out of band because its value must never enter Git:

```bash
kubectl -n pulse create secret generic pulse-agent-token \
  --from-literal=token='<token>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

Validation:

```bash
kubectl -n pulse get daemonset,pods
kubectl -n pulse logs daemonset/pulse-agent --tail=100
kubectl auth can-i --as=system:serviceaccount:pulse:pulse-agent list pods --all-namespaces
```
