# Metrics Server

Metrics Server supplies the Kubernetes resource metrics API used by Headlamp, `kubectl top`, and CPU/memory-based autoscaling.

```bash
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl top nodes
kubectl top pods --all-namespaces
```

It runs two replicas with a PodDisruptionBudget and no persistent storage. Metrics Server is a short-retention autoscaling and current-usage data source; it is not a historical monitoring system. Use Prometheus and Grafana later for retained dashboards and alerts.

Talos kubelet serving certificates do not contain node-IP subject alternative names. The deployment therefore uses `--kubelet-insecure-tls` for kubelet certificate verification while retaining Kubernetes webhook authentication and authorization. Kubelet scrape traffic remains internal to the cluster network.
