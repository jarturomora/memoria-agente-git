"""Pruebas de la experiencia y las salvaguardas de la CLI.

Se reemplazan el cliente y las funciones destructivas para garantizar que las
pruebas nunca contacten con el Elasticsearch de la demostración.
"""

from unittest.mock import MagicMock, patch

import pytest

from src import cli


def test_reset_memory_requires_explicit_confirmation(capsys):
    """Una respuesta distinta de ``BORRAR`` cancela antes de crear el cliente."""
    with patch("builtins.input", return_value="no"), patch.object(cli, "client") as client:
        cli.main(["reset-memory"])

    # ``capsys`` captura lo impreso para poder verificar el mensaje didáctico.
    client.assert_not_called()
    assert "Operación cancelada" in capsys.readouterr().out


def test_reset_memory_confirmed_reports_deleted_count(capsys):
    """El modo no interactivo ejecuta el reset e informa su contador."""
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
    """Los errores del backend se convierten en mensaje y código de salida 1."""
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
