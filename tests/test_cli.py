from unittest.mock import MagicMock, patch

import pytest

from src import cli


def test_reset_memory_requires_explicit_confirmation(capsys):
    with patch("builtins.input", return_value="no"), patch.object(cli, "client") as client:
        cli.main(["reset-memory"])

    client.assert_not_called()
    assert "Operación cancelada" in capsys.readouterr().out


def test_reset_memory_confirmed_reports_deleted_count(capsys):
    es = MagicMock()
    es.ping.return_value = True
    with (
        patch.object(cli, "client", return_value=es),
        patch.object(cli, "ensure_indices") as ensure_indices,
        patch.object(cli, "reset_memories", return_value=4) as reset,
    ):
        cli.main(["reset-memory", "--confirm"])

    ensure_indices.assert_not_called()
    reset.assert_called_once_with(es)
    assert "Recuerdos eliminados: 4" in capsys.readouterr().out


def test_reset_memory_reports_elasticsearch_error(capsys):
    es = MagicMock()
    es.ping.return_value = True
    with (
        patch.object(cli, "client", return_value=es),
        patch.object(cli, "ensure_indices"),
        patch.object(cli, "reset_memories", side_effect=RuntimeError("fallo de Elasticsearch")),
        pytest.raises(SystemExit) as exit_info,
    ):
        cli.main(["reset-memory", "--confirm"])

    assert exit_info.value.code == 1
    assert "Error: fallo de Elasticsearch" in capsys.readouterr().err
