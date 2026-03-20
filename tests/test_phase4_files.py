from pathlib import Path


def test_k8s_manifests_exist():
    required = [
        'k8s/namespace.yaml','k8s/configmap.yaml','k8s/secrets.yaml','k8s/deployments/api-deployment.yaml',
        'k8s/deployments/agent-deployment.yaml','k8s/deployments/watchdog-deployment.yaml','k8s/deployments/learner-deployment.yaml',
        'k8s/deployments/encoder-deployment.yaml','k8s/services/api-service.yaml','k8s/services/redis-service.yaml',
        'k8s/ingress.yaml','k8s/hpa.yaml','k8s/pvc.yaml','k8s/deploy.sh','cli/prometeusz.py','docker/grafana/dashboards/prometeusz.json'
    ]
    for path in required:
        assert Path(path).exists(), path


def test_phase4_yaml_contains_prometeusz_namespace():
    assert 'prometeusz' in Path('k8s/namespace.yaml').read_text()


def test_cli_exists_and_executable():
    path = Path('cli/prometeusz.py')
    assert path.exists()
    assert path.read_text().startswith('#!/usr/bin/env python3')
