#!/usr/bin/env python3
"""
Gerador determinístico do seed SQL para vegapunk-benchmark.
Metas: 56 filmes / 11 gêneros / 6 salas / 101 sessões / 658 reservas.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

DESTINO = Path(__file__).resolve().parent / "init" / "02_seed.sql"

out = []

# ---------------------------------------------------------------------------
# FILMES (56)
# ---------------------------------------------------------------------------
filmes = [
    # Ação (7) — filme_id 1..7
    (1,'O Último Combate','Soldado luta pela sobrevivência em missão suicida.','Carlos Mendes','Ação',120),
    (2,'Força Bruta','Agente infiltrado desmantelou rede criminosa internacional.','Roberto Alves','Ação',108),
    (3,'Resgate Impossível','Equipe de elite tenta resgatar reféns em território hostil.','Ana Ferreira','Ação',132),
    (4,'Código de Guerra','Coronel descobre traição dentro de suas próprias fileiras.','Paulo Siqueira','Ação',115),
    (5,'Operação Trovão','Missão secreta para neutralizar arma biológica.','Marcos Lima','Ação',125),
    (6,'A Missão Final','Veterano é convocado para uma última operação perigosa.','Juliana Costa','Ação',118),
    (7,'Zona de Conflito','Repórter de guerra fica presa em campo de batalha.','Fernando Santos','Ação',130),
    # Comédia (6) — filme_id 8..13
    (8,'Família em Caos','Reunião familiar vira série de situações absurdas.','Luís Moreira','Comédia',95),
    (9,'Confusão Total','Troca de identidades leva a situações hilariantes.','Sônia Barros','Comédia',102),
    (10,'O Vizinho Perfeito','Novo vizinho perfeito demais revela segredos obscuros.','Rafael Torres','Comédia',98),
    (11,'Amor às Avessas','Casal decide fazer tudo ao contrário por um mês.','Claudia Nunes','Comédia',105),
    (12,'O Melhor Casamento','Planejador apaixona-se pela noiva do cliente.','Thiago Ramos','Comédia',110),
    (13,'Dois Idiotas e um Destino','Dois amigos perdidos cruzam o Brasil de bicicleta.','Patrícia Leal','Comédia',92),
    # Drama (6) — filme_id 14..19
    (14,'A Última Carta','Filha descobre cartas do pai morto que mudam tudo.','Marcela Oliveira','Drama',140),
    (15,'Entre Laços','Família enfrenta crise após revelação de segredo.','Eduardo Vieira','Drama',128),
    (16,'O Preço do Silêncio','Advogada defende inocente mas esconde a própria culpa.','Renata Campos','Drama',135),
    (17,'Caminhos que se Cruzam','Três estranhos descobrem ligação inesperada.','Gabriel Pinto','Drama',122),
    (18,'A Promessa','Pai cumpre promessa feita ao filho antes de morrer.','Helena Freitas','Drama',118),
    (19,'Sombras do Passado','Mulher retorna à cidade natal e enfrenta traumas.','Diego Cardoso','Drama',145),
    # Terror (5) — filme_id 20..24
    (20,'A Casa do Fim','Família se muda para mansão com história sinistra.','Bruno Teixeira','Terror',95),
    (21,'Noite Eterna','Cidade perde a luz solar e criaturas tomam as ruas.','Larissa Fonseca','Terror',88),
    (22,'O Chamado das Trevas','Jovem ouve vozes que a guiam a rituais obscuros.','Ricardo Batista','Terror',102),
    (23,'Presença Sombria','Fotógrafo captura entidade em imagens de vila.','Amanda Cruz','Terror',90),
    (24,'A Última Testemunha','Única sobrevivente é perseguida pelo assassino.','Leandro Souza','Terror',98),
    # Ficção Científica (6) — filme_id 25..30
    (25,'Além das Estrelas','Tripulação descobre planeta habitável com segredo mortal.','Isabela Rocha','Ficção Científica',140),
    (26,'Protocolo Omega','IA decide que a humanidade é uma ameaça e age.','Caio Nascimento','Ficção Científica',128),
    (27,'A Última Colônia','Colônia marciana luta por independência da Terra.','Fernanda Gomes','Ficção Científica',155),
    (28,'Singularidade','Cientista atinge singularidade e muda o mundo.','Victor Carvalho','Ficção Científica',132),
    (29,'Horizonte de Eventos','Nave é sugada por buraco negro e emerge em outro tempo.','Natalia Ribeiro','Ficção Científica',148),
    (30,'O Projeto Genesis','Governo cria humanidade geneticamente perfeita.','André Medeiros','Ficção Científica',138),
    # Animação (5) — filme_id 31..35
    (31,'A Grande Aventura','Coelho corajoso parte em busca da floresta perdida.','Studio Animax','Animação',95),
    (32,'O Reino Encantado','Princesa descobre que seu reino é guardado por magia.','Studio Pixel','Animação',88),
    (33,'Viagem ao Centro do Sonho','Menino entra no mundo dos sonhos para salvar irmã.','Studio Lumiere','Animação',102),
    (34,'Os Guardiões da Floresta','Animais unem forças para salvar a floresta.','Studio Natureza','Animação',90),
    (35,'O Pequeno Explorador','Robozinho explora galáxia em busca de sua origem.','Studio Cosmos','Animação',85),
    # Romance (5) — filme_id 36..40
    (36,'Amor em Paris','Escritora brasileira se apaixona em Paris.','Camila Duarte','Romance',112),
    (37,'O Último Verão','Dois jovens vivem romance impossível num verão.','Felipe Martins','Romance',105),
    (38,'Dois Corações','Ex-casal se reencontra numa viagem inesperada.','Vanessa Almeida','Romance',118),
    (39,'A Segunda Chance','Viúvo aprende a amar novamente com ajuda de vizinha.','Rodrigo Pereira','Romance',108),
    (40,'Sempre Te Amarei','Casal separado pela guerra se busca por décadas.','Marina Azevedo','Romance',122),
    # Suspense (5) — filme_id 41..45
    (41,'O Desaparecimento','Detetive investiga sumiço de criança em cidade pequena.','Sergio Monteiro','Suspense',118),
    (42,'Sombras da Noite','Jornalista descobre conspiração que ameaça sua vida.','Tatiana Borges','Suspense',125),
    (43,'A Testemunha','Homem assiste crime e entra em programa de proteção.','Gustavo Araujo','Suspense',112),
    (44,'Jogo Mortal','Criminoso cria jogos mortais transmitidos ao vivo.','Priscila Lima','Suspense',130),
    (45,'O Segredo da Mansão','Herdeiros encontram cadáver na nova propriedade.','Jonas Ferreira','Suspense',108),
    # Documentário (4) — filme_id 46..49
    (46,'Amazônia: O Último Paraíso','Expedição revela biodiversidade ameaçada da Amazônia.','Eco Films','Documentário',90),
    (47,'A Vida nas Profundezas','Exploração dos oceanos mais profundos do planeta.','Ocean Docs','Documentário',85),
    (48,'Grandes Civilizações','Arqueólogos revelam segredos de civilizações antigas.','History Prod.','Documentário',95),
    (49,'O Mundo dos Oceanos','Jornada visual pelos ecossistemas marinhos.','Blue Planet BR','Documentário',88),
    # Aventura (4) — filme_id 50..53
    (50,'A Ilha Perdida','Grupo naufraga em ilha com segredo milenar.','Flávio Nogueira','Aventura',128),
    (51,'Em Busca do Tesouro','Mapa antigo leva expedição a tesouro inca.','Carolina Mello','Aventura',118),
    (52,'O Explorador','Botânico adentra selva proibida em busca de planta rara.','Tiago Braga','Aventura',135),
    (53,'Além dos Limites','Alpinistas enfrentam tempestade mortal no Himalaia.','Pedro Saraiva','Aventura',122),
    # Musical (3) — filme_id 54..56
    (54,'O Show da Vida','Jovem cantor vence batalhas para chegar ao estrelato.','Sandra Lopes','Musical',115),
    (55,'Melodias do Coração','Músico reencontra inspiração após tragédia pessoal.','Henrique Castro','Musical',108),
    (56,'A Grande Apresentação','Escola de música prepara espetáculo histórico.','Lidia Torres','Musical',125),
]

# ---------------------------------------------------------------------------
# SALAS (6)  → ticket_price fixo por sala
# ---------------------------------------------------------------------------
salas = [
    (1,'Sala 1',100),
    (2,'Sala 2',80),
    (3,'Sala 3',120),
    (4,'Sala 4',60),
    (5,'Sala 5',150),
    (6,'Sala VIP',40),
]
ticket_price = {1:Decimal('28.00'),2:Decimal('25.00'),3:Decimal('30.00'),
                4:Decimal('22.00'),5:Decimal('35.00'),6:Decimal('50.00')}

# ---------------------------------------------------------------------------
# SESSÕES (101)
# Distribuição:
#   filme_id=1 : 15 sessões  → líder indiscutível
#   filme_id=2..10 (9 filmes): 5 cada  = 45
#   filme_id=11..30 (20 filmes): 2 cada = 40
#   filme_id=31 : 1 sessão
#   filme_id=32..56 : 0
# Total: 15+45+40+1 = 101
# ---------------------------------------------------------------------------
filme_duracao = {f[0]: f[5] for f in filmes}

def dt(year,month,day,hour,minute=0):
    return datetime(year,month,day,hour,minute)

# Horários disponíveis (hora)
HORARIOS = [14,16,18,20]

# Gera lista de (filme_id, sala_id, start_time)
sessions_raw = []

def add(film_id, sala_id, start):
    dur = filme_duracao[film_id]
    end = start + timedelta(minutes=dur)
    sessions_raw.append((film_id, sala_id, start, end, ticket_price[sala_id]))

# === Filme 1 — 15 sessões (Sala 1, 3, 5 rotativo, Jan e Fev)
for i in range(15):
    day   = 2 + i * 6         # dias 2,8,14,20,26,32→fev... espaçado
    month = 1
    if day > 31:
        day -= 31; month = 2
    if day > 28:
        day -= 28; month = 3
    sala = [1,3,5][i%3]
    hora = HORARIOS[i%4]
    add(1, sala, dt(2025,month,day,hora))

# === Filmes 2..10 — 5 sessões cada
times_block = [
    dt(2025,1,3,14), dt(2025,1,10,16), dt(2025,1,17,18), dt(2025,1,24,20), dt(2025,2,1,14),
]
for idx, fid in enumerate(range(2,11)):   # 9 filmes
    for j, base in enumerate(times_block):
        offset_days = idx * 2
        st = base + timedelta(days=offset_days)
        sala = [1,2,3,4,5,6][( idx+j )%6]
        add(fid, sala, st)

# === Filmes 11..30 — 2 sessões cada
base_date = datetime(2025,2,1,14)
for idx, fid in enumerate(range(11,31)):  # 20 filmes
    for j in range(2):
        st = base_date + timedelta(days=idx*3+j*1, hours=j*2)
        sala = [2,4,6][ (idx+j) % 3 ]
        add(fid, sala, st)

# === Filme 31 — 1 sessão
add(31, 2, dt(2025,3,15,16))

assert len(sessions_raw) == 101, f"Esperado 101, got {len(sessions_raw)}"

# Mapeia sessao_id → ticket_price
sessao_ticket = {}
for i, s in enumerate(sessions_raw, start=1):
    sessao_ticket[i] = s[4]

# ---------------------------------------------------------------------------
# RESERVAS (658)
# Usuários fixos (estilo UUID Keycloak, 30 usuários)
# Líder: user-001 → 80 reservas
# Distribuição status: ~70% CONFIRMED, ~20% CANCELLED, ~10% PENDING
# ---------------------------------------------------------------------------
users = [f'kc-user-{str(i).zfill(3)}' for i in range(1,31)]  # kc-user-001 .. kc-user-030

# Reservas por usuário (total = 658)
# user-001 = 80 (líder), user-002=45, user-003=40, outros decrescentes
reservas_por_usuario = [80,45,40,35,30,30,29,28,26,25,24,23,22,21,20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,5]
assert sum(reservas_por_usuario) == 658, f"Soma = {sum(reservas_por_usuario)}"

# Status cycle: 7 CONFIRMED, 2 CANCELLED, 1 PENDING (exato 70/20/10)
STATUS_CYCLE = (['CONFIRMED']*7 + ['CANCELLED']*2 + ['PENDING']*1)

reservas = []
rid = 1
global_idx = 0
created_base = datetime(2025,1,1,10,0,0)

for u_idx, (user, n_reservas) in enumerate(zip(users, reservas_por_usuario)):
    # Sessões disponíveis para este usuário (todas as 101, ciclo)
    for k in range(n_reservas):
        sessao_id   = (global_idx % 101) + 1
        n_ingressos = (k % 4) + 1           # 1,2,3,4 cíclico
        tp          = sessao_ticket[sessao_id]
        preco_total = tp * n_ingressos
        status      = STATUS_CYCLE[global_idx % 10]
        created_at  = created_base + timedelta(days=global_idx % 89, hours=u_idx % 12)
        reservas.append((rid, user, sessao_id, n_ingressos, preco_total, status, created_at))
        rid += 1
        global_idx += 1

assert len(reservas) == 658, f"Esperado 658, got {len(reservas)}"

# Verifica distribuição de status
confirmed = sum(1 for r in reservas if r[5]=='CONFIRMED')
cancelled = sum(1 for r in reservas if r[5]=='CANCELLED')
pending   = sum(1 for r in reservas if r[5]=='PENDING')
print(f"Status: CONFIRMED={confirmed} ({confirmed/658*100:.1f}%), CANCELLED={cancelled} ({cancelled/658*100:.1f}%), PENDING={pending} ({pending/658*100:.1f}%)")

# ---------------------------------------------------------------------------
# GERA SQL
# ---------------------------------------------------------------------------
lines = []
lines.append("-- =============================================================================")
lines.append("-- VEGAPUNK BENCHMARK — SEED DETERMINÍSTICO")
lines.append("-- 56 filmes / 11 gêneros / 6 salas / 101 sessões / 658 reservas")
lines.append("-- Gerado por gerar_seed.py — não editar manualmente")
lines.append("-- =============================================================================")
lines.append("")

# FILMES
lines.append("-- ---------------------------------------------------------------------------")
lines.append("-- FILMES (56)")
lines.append("-- ---------------------------------------------------------------------------")
lines.append("INSERT INTO filmes (id, titulo, sinopse, diretor, genero, duracao_em_minutos) VALUES")
rows = []
for f in filmes:
    titulo   = f[1].replace("'","''")
    sinopse  = f[2].replace("'","''")
    diretor  = f[3].replace("'","''")
    genero   = f[4].replace("'","''")
    rows.append(f"  ({f[0]}, '{titulo}', '{sinopse}', '{diretor}', '{genero}', {f[5]})")
lines.append(",\n".join(rows) + ";")
lines.append("SELECT setval('filmes_id_seq', 56);")
lines.append("")

# SALAS
lines.append("-- ---------------------------------------------------------------------------")
lines.append("-- SALAS (6)")
lines.append("-- ---------------------------------------------------------------------------")
lines.append("INSERT INTO salas (id, nome, capacidade) VALUES")
rows = []
for s in salas:
    rows.append(f"  ({s[0]}, '{s[1]}', {s[2]})")
lines.append(",\n".join(rows) + ";")
lines.append("SELECT setval('salas_id_seq', 6);")
lines.append("")

# SESSOES
lines.append("-- ---------------------------------------------------------------------------")
lines.append("-- SESSÕES (101)")
lines.append("-- Filme 1 (O Último Combate): 15 sessões — líder indiscutível")
lines.append("-- ---------------------------------------------------------------------------")
lines.append("INSERT INTO sessoes (id, filme_id, sala_id, start_time, end_time, ticket_price) VALUES")
rows = []
for i, s in enumerate(sessions_raw, start=1):
    film_id, sala_id, start, end, tp = s
    rows.append(f"  ({i}, {film_id}, {sala_id}, '{start}', '{end}', {tp})")
lines.append(",\n".join(rows) + ";")
lines.append("SELECT setval('sessoes_id_seq', 101);")
lines.append("")

# RESERVAS
lines.append("-- ---------------------------------------------------------------------------")
lines.append("-- RESERVAS (658)")
lines.append(f"-- CONFIRMED={confirmed}, CANCELLED={cancelled}, PENDING={pending}")
lines.append("-- Líder em reservas: kc-user-001 (80 reservas)")
lines.append("-- preco_total = numero_de_ingressos × ticket_price da sessão")
lines.append("-- ---------------------------------------------------------------------------")
lines.append("INSERT INTO reservas (id, usuario_id, sessao_id, numero_de_ingressos, preco_total, status, created_at) VALUES")
rows = []
for r in reservas:
    rid2, user, sid2, n_ing, preco, status, cat = r
    rows.append(f"  ({rid2}, '{user}', {sid2}, {n_ing}, {preco}, '{status}', '{cat}')")
lines.append(",\n".join(rows) + ";")
lines.append("SELECT setval('reservas_id_seq', 658);")
lines.append("")

sql_content = "\n".join(lines)

with open(DESTINO, 'w') as f:
    f.write(sql_content)

print(f"02_seed.sql gerado: {len(sql_content)} bytes")
print(f"Sessões por filme-1: {sum(1 for s in sessions_raw if s[0]==1)}")
print(f"Reservas por kc-user-001: {reservas_por_usuario[0]}")

# Verifica unicidade do líder em sessões
from collections import Counter
sess_por_filme = Counter(s[0] for s in sessions_raw)
top2 = sess_por_filme.most_common(2)
print(f"Top-2 filmes em sessões: {top2}")
print("Unicidade líder sessões OK" if top2[0][1] > top2[1][1] else "ERRO: empate no líder!")
print("Unicidade líder reservas OK" if reservas_por_usuario[0] > reservas_por_usuario[1] else "ERRO: empate no líder!")
