# Inconsistência — módulo Ponto

- O schema/model suportam `tipo` = `entrada`, `saida`, `pausa`.
- A tela de ponto pensada, foi desenhada com 4 marcações (entrada/saída/entrada/saída) e não expõe `pausa`.

## Propostas (decidir)

- **Intervalo almoço**
  - Usar `pausa` (alinha com schema/README), ou
  - Manter `saida` + `entrada` como “intervalo”, e `pausa` ficar para outra pausa.

- **Quem bate ponto**
  - RH seleciona um funcionário e registra (coerente com README: `Funcionario` que explicita que o usuario não logar no sistema), ou
  - Usuário logado bate o próprio ponto (exige amarrar `UserProfile.funcionario` e ajustar README/fluxo que foi proposto por ia).
