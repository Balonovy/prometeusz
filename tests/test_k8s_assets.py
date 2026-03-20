from pathlib import Path


def test_k8s_manifests_exist():
    required = [
        'k8s/namespace.yaml',
        'k8s/configmap.yaml',
        'k8s/secrets.yaml',
        'k8s/deployments/api-deployment.yaml',
        'k8s/deployments/agent-deployment.yaml',
        'k8s/deployments/watchdog-deployment.yaml',
        'k8s/deployments/learner-deployment.yaml',
        'k8s/deployments/encoder-deployment.yaml',
        'k8s/services/api-service.yaml',
        'k8s/services/redis-service.yaml',
        'k8s/ingress.yaml',
        'k8s/hpa.yaml',
        'k8s/pvc.yaml',
        'k8s/deploy.sh',
    ]
    assert all(Path(path).exists() for path in required)
