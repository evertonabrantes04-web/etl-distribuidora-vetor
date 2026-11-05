from datetime import date
from io import StringIO
from unittest.mock import MagicMock, patch

from django.test import TestCase

from .models import CacheCEP, Cliente, DicionarioBairro, LogAuditoria
from .pipeline import (
    converter_data,
    executar,
    limpar_cep,
    limpar_cnpj,
    limpar_email,
    limpar_telefone,
    normalizar_chave_bairro,
)


class NormalizacaoUnitariaTests(TestCase):
    def test_normalizar_chave_bairro_remove_acentos_e_uf(self):
        self.assertEqual(normalizar_chave_bairro("Águas Claras/DF"), "aguas claras")
        self.assertEqual(normalizar_chave_bairro("  Taguatinga - DF "), "taguatinga")
        self.assertEqual(normalizar_chave_bairro("Sul (Águas Claras)"), "sul (aguas claras)")

    def test_limpar_cnpj_aplica_mascara(self):
        self.assertEqual(limpar_cnpj("27868011280598"), "27.868.011/2805-98")
        self.assertEqual(limpar_cnpj("84.959.310/3413-16"), "84.959.310/3413-16")
        self.assertIsNone(limpar_cnpj("123"))

    def test_limpar_telefone_remove_ddi_e_formata(self):
        self.assertEqual(limpar_telefone("+55 61 95386-2084"), "(61) 95386-2084")
        self.assertEqual(limpar_telefone("61970855700"), "(61) 97085-5700")
        self.assertEqual(limpar_telefone("61 3970-2193"), "(61) 3970-2193")

    def test_limpar_email_remove_acentos(self):
        self.assertEqual(
            limpar_email("Contato@ComercialSão.com.br"),
            "contato@comercialsao.com.br",
        )

    def test_limpar_cep_descarta_zerado_ou_vazio(self):
        self.assertEqual(limpar_cep("00000-000"), "")
        self.assertEqual(limpar_cep(None), "")
        self.assertEqual(limpar_cep("71926750"), "71926-750")

    def test_converter_data_multiformato(self):
        self.assertEqual(converter_data("2022-06-21"), date(2022, 6, 21))
        self.assertEqual(converter_data("28/02/2022"), date(2022, 2, 28))
        self.assertEqual(converter_data("08-01-2022"), date(2022, 1, 8))
        self.assertEqual(converter_data("Dec 24, 2023"), date(2023, 12, 24))
        self.assertEqual(converter_data("jul 21, 2022"), date(2022, 7, 21))


class PipelineIntegracaoMockTests(TestCase):
    @patch("etl.pipeline.requests.get")
    def test_pipeline_resolve_conflito_cep_e_gera_auditoria_sem_internet(self, mock_get):
        resposta_falsa = MagicMock()
        resposta_falsa.status_code = 200
        resposta_falsa.json.return_value = {
            "cep": "72140-010",
            "bairro": "Taguatinga Norte",
            "localidade": "Brasília",
            "uf": "DF",
        }
        mock_get.return_value = resposta_falsa

        csv_simulado = (
            "id_cliente;razao_social;cnpj;telefone;email;bairro_informado;cep;cidade;uf;data_cadastro;vendedor_responsavel\n"
            "CLI0002;Comercial São Judas;28327648350305;+55 61 95386-2084;contato@comercialsão.com.br;Sul (Aguas Claras);72140-010;Brasília;DF;Dec 24, 2023;Camila Torres\n"
            "CLI0047;Mercadinho Sem Endereço;82.675.869/2617-96;61914391105;contato@semendereco.com.br;;;Brasília;DF;2022-06-23;Juliana Reis\n"
        )

        execucao = executar(StringIO(csv_simulado), "teste_mock.csv")

        self.assertTrue(execucao.sucesso)
        self.assertEqual(execucao.lidas, 2)
        self.assertEqual(execucao.carregadas, 2)
        self.assertEqual(execucao.em_revisao, 1)
        self.assertEqual(mock_get.call_count, 1)
        self.assertTrue(CacheCEP.objects.filter(cep="72140-010").exists())

        cli2 = Cliente.objects.get(id_cliente="CLI0002")
        self.assertEqual(cli2.bairro_tratado, "Taguatinga")
        self.assertEqual(cli2.status_validacao, "DIVERGENCIA_CEP_CORRIGIDA")
        self.assertEqual(cli2.cnpj, "28.327.648/3503-05")
        self.assertEqual(cli2.email, "contato@comercialsao.com.br")

        cli47 = Cliente.objects.get(id_cliente="CLI0047")
        self.assertEqual(cli47.bairro_tratado, "Não Informado")
        self.assertEqual(cli47.status_validacao, "REVISAO_MANUAL")

        campos_auditados = set(
            LogAuditoria.objects.filter(id_cliente="CLI0002").values_list("campo", flat=True)
        )
        self.assertSetEqual(
            campos_auditados,
            {"cnpj", "telefone", "email", "data_cadastro", "bairro_informado"},
        )

    @patch("etl.pipeline.requests.get")
    def test_dicionario_dinamico_do_banco_sobrescreve_variante(self, mock_get):
        DicionarioBairro.objects.create(
            variante_normalizada="setor habitacional sol nascente",
            nome_canonico="Sol Nascente",
        )
        csv_simulado = (
            "id_cliente;razao_social;cnpj;telefone;email;bairro_informado;cep;cidade;uf;data_cadastro;vendedor_responsavel\n"
            "CLI0099;Mercado Sol;28.327.648/3503-05;(61) 98433-1053;ok@ok.com.br;Setor Habitacional Sol Nascente;;Brasília;DF;2023-10-07;Bruno\n"
        )
        executar(StringIO(csv_simulado), "teste_dic.csv")
        cli = Cliente.objects.get(id_cliente="CLI0099")
        self.assertEqual(cli.bairro_tratado, "Sol Nascente")
        mock_get.assert_not_called()