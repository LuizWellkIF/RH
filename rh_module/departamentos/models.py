from django.db import models
# Create your models here.

'''
Modelo Departamento, representando os departamentos da empresa. Cada departamento tem um ID único, um nome e uma sigla.
A sigla é única e é convertida para maiúscula e sem espaços em branco antes de ser salva, garantindo a consistência dos dados.
'''
class Departamento(models.Model):
    id_departamento = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=250)
    sigla = models.CharField(max_length=50, unique=True)
    
    class Meta:
        db_table = 'departamento'
        ordering = ['nome']
        
    def __str__(self):
        return f'{self.sigla} - {self.nome}'