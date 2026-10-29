from django.db import models


class Cliente(models.Model):
    id_cliente = models.CharField(max_length=20, unique=True)
    razao_social = models.CharField(max_length=150)
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(max_length=150)
    bairro_informado = models.CharField(max_length=100, blank=True)
    bairro_tratado = models.CharField(max_length=100)
    cep = models.CharField(max_length=9, blank=True)
    cidade = models.CharField(max_length=60)
    uf = models.CharField(max_length=2)
    data_cadastro = models.DateField()
    vendedor_responsavel = models.CharField(max_length=100)
    status_validacao = models.CharField(max_length=40, default="VALIDADO")

    class Meta:
        ordering = ["id_cliente"]

    def __str__(self):
        return f"{self.id_cliente} - {self.razao_social} ({self.bairro_tratado})"


class Execucao(models.Model):
    iniciada_em = models.DateTimeField(auto_now_add=True)
    arquivo = models.CharField(max_length=255)
    lidas = models.PositiveIntegerField(default=0)
    carregadas = models.PositiveIntegerField(default=0)
    descartadas = models.PositiveIntegerField(default=0)
    em_revisao = models.PositiveIntegerField(default=0)
    sucesso = models.BooleanField(default=False)
    mensagem = models.TextField(blank=True)

    class Meta:
        ordering = ["-iniciada_em"]
        verbose_name = "execução"
        verbose_name_plural = "execuções"

    def __str__(self):
        return f"{self.iniciada_em:%d/%m/%Y %H:%M} - {self.arquivo}"


class LogAuditoria(models.Model):
    execucao = models.ForeignKey(Execucao, on_delete=models.CASCADE, related_name="logs")
    id_cliente = models.CharField(max_length=20)
    campo = models.CharField(max_length=50)
    valor_original = models.TextField(blank=True, null=True)
    valor_tratado = models.TextField(blank=True, null=True)
    criterio = models.CharField(max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id_cliente", "campo"]


class DicionarioBairro(models.Model):
    variante_normalizada = models.CharField(max_length=100, unique=True)
    nome_canonico = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.variante_normalizada} -> {self.nome_canonico}"


class CacheCEP(models.Model):
    cep = models.CharField(max_length=9, unique=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=60, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    fonte = models.CharField(max_length=50, default="BrasilAPI/ViaCEP")
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cep} -> {self.bairro}"