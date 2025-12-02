import pygame
import sys
import random
import math
import json
import os

# --- 1. CONFIGURAÇÕES GLOBAIS ---
LARGURA_TELA = 1024
ALTURA_TELA = 768
TITULO = "Conserta-Rural-Junior"
FPS = 60

# Cores
PRETO = (0, 0, 0)
AZUL = (0, 0, 255)
AMARELO = (255, 255, 0)
VERDE = (0, 255, 0)
VERMELHO = (255, 0, 0)
MARROM = (139, 69, 19)
CINZA = (100, 100, 100)
AZUL_ESCURO = (0, 0, 100)
LARANJA = (255, 165, 0)
DOURADO = (255, 215, 0)
BRANCO = (255, 255, 255)

COLS_X = [180, 340, 500, 660, 820]
ROWS_Y = [108, 223, 338, 453, 568]

TEMPO_LIMITE_NIVEL = 70
ARQUIVO_SCORES = "highscores.json"

# --- 2. CLASSES ---

class Heroi(pygame.sprite.Sprite):
    def __init__(self, modo_jogo, debug=False):
        super().__init__()
        self.modo = modo_jogo
        self.modo_debug = debug
        self.image = pygame.Surface((32, 32))
        
        if self.modo_debug:
            self.image.fill((0, 255, 255)) 
        else:
            self.image.fill(AZUL)
            
        self.rect = self.image.get_rect()
        self.vidas = 3
        
        self.pontuacao = 0
        self.contagem_consertos = 0 
        self.itens_coletados = 0    
        
        self.invencivel = False
        self.tempo_invencivel = 0
        self.duracao_invencibilidade_atual = 2000 
        
        self.ultimo_conserto = 0
        self.cooldown_conserto = 400
        
        self.velocidade_x = 0
        self.velocidade_y = 0
        self.gravidade = 0.8
        self.forca_pulo = -15
        self.no_chao = False
        self.ultima_posicao_segura = (0, 0) 
        
        self.coluna_atual = 2
        self.andar_atual = 4
        self.pulando_classico = False
        self.pulo_progresso = 0.0
        self.pulo_inicio = (0,0)
        self.pulo_fim = (0,0)
        self.velocidade_animacao_pulo = 0.05 
        
        self.resetar_posicao()

    def resetar_posicao(self):
        if self.modo == "CLASSICO":
            self.coluna_atual = 2
            self.andar_atual = 4
            self.rect.x = COLS_X[self.coluna_atual] + 4
            self.rect.y = ROWS_Y[self.andar_atual]
        else:
            x_inicial = COLS_X[2] + 4
            y_inicial = ROWS_Y[4]
            self.rect.x = x_inicial
            self.rect.y = y_inicial
            self.velocidade_y = 0
            self.ultima_posicao_segura = (self.rect.centerx, self.rect.bottom) 

    def ativar_invencibilidade(self, duracao):
        self.invencivel = True
        self.tempo_invencivel = pygame.time.get_ticks()
        self.duracao_invencibilidade_atual = duracao

    def tomar_dano(self):
        if self.modo_debug or self.invencivel:
            return False
        self.vidas -= 1
        if self.vidas > 0:
            self.ativar_invencibilidade(2000)
        return True 

    def update(self):
        if self.invencivel and not self.modo_debug:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_invencivel > self.duracao_invencibilidade_atual:
                self.invencivel = False
                self.image.set_alpha(255) 
            else:
                if (agora // 100) % 2 == 0: self.image.set_alpha(0)
                else: self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

        if self.modo == "LIVRE": self.update_livre()
        else: self.update_classico()

    def update_livre(self):
        self.velocidade_x = 0
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]: self.velocidade_x = -5
        if teclas[pygame.K_RIGHT]: self.velocidade_x = 5
        
        quer_descer = False
        if teclas[pygame.K_DOWN]: quer_descer = True
            
        self.rect.x += self.velocidade_x
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > LARGURA_TELA: self.rect.right = LARGURA_TELA
        
        self.velocidade_y += self.gravidade
        self.rect.y += self.velocidade_y
        self.no_chao = False
        
        if not quer_descer:
            colisoes = pygame.sprite.spritecollide(self, plataformas, False)
            for bloco in colisoes:
                if self.velocidade_y > 0 and self.rect.bottom < bloco.rect.bottom + 10:
                    self.rect.bottom = bloco.rect.top
                    self.velocidade_y = 0
                    self.no_chao = True
                    self.ultima_posicao_segura = (self.rect.centerx, self.rect.bottom) 
        else:
            self.no_chao = False

        if self.rect.bottom > ALTURA_TELA:
            levou_dano = self.tomar_dano()
            self.rect.centerx, self.rect.bottom = self.ultima_posicao_segura
            self.velocidade_y = 0
            self.no_chao = True 
            if levou_dano: print("Caiu! Dano aplicado.")

    def pular_livre(self):
        if self.no_chao:
            self.velocidade_y = self.forca_pulo
            self.no_chao = False

    def update_classico(self):
        if self.pulando_classico:
            self.pulo_progresso += self.velocidade_animacao_pulo
            if self.pulo_progresso >= 1.0:
                self.pulo_progresso = 1.0
                self.pulando_classico = False
                self.rect.x = COLS_X[self.coluna_atual] + 4
                self.rect.y = ROWS_Y[self.andar_atual]
            else:
                ix, iy = self.pulo_inicio
                fx, fy = self.pulo_fim
                novo_x = ix + (fx - ix) * self.pulo_progresso
                arco = 50 * 4 * self.pulo_progresso * (1 - self.pulo_progresso)
                base_y = iy + (fy - iy) * self.pulo_progresso
                self.rect.x = int(novo_x)
                self.rect.y = int(base_y - arco)

    def mover_classico(self, dx, dy):
        if self.pulando_classico: return
        nc, na = self.coluna_atual + dx, self.andar_atual + dy
        if 0 <= nc < 5 and 1 <= na < 5:
            self.pulando_classico = True
            self.pulo_progresso = 0.0
            self.pulo_inicio = (self.rect.x, self.rect.y)
            self.coluna_atual, self.andar_atual = nc, na
            self.pulo_fim = (COLS_X[nc] + 4, ROWS_Y[na])

class ItemBonus(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(DOURADO)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.tempo_nascimento = pygame.time.get_ticks()
        self.tempo_vida = 7000 

    def update(self):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_nascimento > self.tempo_vida:
            self.kill()

class Inimigo(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill(VERMELHO)
        self.rect = self.image.get_rect()
        self.limite_esq = 180
        self.limite_dir = 860 
        self.rect.centerx = LARGURA_TELA // 2
        self.rect.y = 90
        
        self.velocidade_base = 4
        self.velocidade = 4
        self.velocidade_projetil = 6
        
        self.estado = "PATRULHA"
        self.ultimo_troca_estado = pygame.time.get_ticks()
        self.tempo_para_proxima_troca = random.randint(3000, 6000)
        
        self.ultimo_tiro = 0
        self.intervalo_tiro_base = 600
        self.intervalo_tiro_atual = 600
        
        self.pode_entrar_furia = False
        self.tipo_ataque_especial = "NENHUM"
        self.pausa_pos_ataque = 0 
        self.ultima_coluna_atacada = None

        self.tijolos_pendentes = 0     
        self.tempo_ultimo_burst = 0    
        self.delay_burst = 200         

    def atualizar_dificuldade(self, nivel, max_niveis, nome_dificuldade):
        self.velocidade = self.velocidade_base + (nivel * 0.5)
        novo_intervalo = self.intervalo_tiro_base - (nivel * 40)
        self.intervalo_tiro_atual = max(250, novo_intervalo)
        self.velocidade_projetil = 3 + (nivel * 0.5)
        
        self.pode_entrar_furia = False
        self.tipo_ataque_especial = "NENHUM"
        niveis_para_fim = max_niveis - nivel + 1
        
        if nome_dificuldade == "DIFICILIMO" and niveis_para_fim <= 4:
            self.pode_entrar_furia = True
            self.tipo_ataque_especial = "LEQUE"
        elif nome_dificuldade == "DIFICIL" and niveis_para_fim <= 2:
            self.pode_entrar_furia = True
            self.tipo_ataque_especial = "METRALHADORA"

    def update(self):
        agora = pygame.time.get_ticks()
        
        if self.tijolos_pendentes > 0 or agora < self.pausa_pos_ataque:
            return 

        if not self.pode_entrar_furia:
            self.estado = "PATRULHA"
            self.image.fill(VERMELHO)
        else:
            if agora - self.ultimo_troca_estado > self.tempo_para_proxima_troca:
                self.ultimo_troca_estado = agora
                if self.estado == "PATRULHA":
                    self.estado = "FURIA"
                    self.tempo_para_proxima_troca = random.randint(2000, 4000)
                    self.image.fill((255, 100, 0)) 
                else:
                    self.estado = "PATRULHA"
                    self.tempo_para_proxima_troca = random.randint(3000, 6000)
                    self.image.fill(VERMELHO)

        if self.estado == "PATRULHA":
            self.rect.x += self.velocidade
            if self.rect.right >= self.limite_dir:
                self.velocidade = -abs(self.velocidade)
            if self.rect.left <= self.limite_esq:
                self.velocidade = abs(self.velocidade)
        elif self.estado == "FURIA":
            pass

    def tentar_atirar(self):
        agora = pygame.time.get_ticks()
        lista_tijolos = []

        if self.tijolos_pendentes > 0:
            if agora - self.tempo_ultimo_burst > self.delay_burst:
                t = Tijolo(self.rect.centerx, self.rect.bottom, 0, self.velocidade_projetil)
                lista_tijolos.append(t)
                self.tijolos_pendentes -= 1
                self.tempo_ultimo_burst = agora
                if self.tijolos_pendentes == 0:
                    self.pausa_pos_ataque = agora + 2000 
                    self.ultimo_tiro = agora
            return lista_tijolos

        if agora < self.pausa_pos_ataque:
            return []
            
        if self.estado == "FURIA":
            intervalo = self.intervalo_tiro_atual / 2.5 
        else:
            intervalo = self.intervalo_tiro_atual

        if agora - self.ultimo_tiro > intervalo:
            
            if self.estado == "PATRULHA":
                coluna_x_esquerda = min(COLS_X, key=lambda x: abs((x + 20) - self.rect.centerx))
                centro_alvo = coluna_x_esquerda + 20
                
                if abs(self.rect.centerx - centro_alvo) <= self.velocidade:
                    if coluna_x_esquerda == self.ultima_coluna_atacada:
                        return [] 
                    
                    self.rect.centerx = centro_alvo 
                    self.ultima_coluna_atacada = coluna_x_esquerda
                    self.tijolos_pendentes = 3
                    self.tempo_ultimo_burst = agora - self.delay_burst
                else:
                    return []

            elif self.estado == "FURIA":
                self.ultimo_tiro = agora
                origens = [self.rect.centerx - 25, self.rect.centerx + 25]
                
                if self.tipo_ataque_especial == "LEQUE":
                    for x_origem in origens:
                        angulo_graus = random.uniform(-35, 35)
                        angulo_rad = math.radians(angulo_graus)
                        vx = self.velocidade_projetil * math.sin(angulo_rad)
                        vy = self.velocidade_projetil * math.cos(angulo_rad)
                        t = Tijolo(x_origem, self.rect.bottom, vx, vy)
                        lista_tijolos.append(t)
                else:
                    for x_origem in origens:
                        t = Tijolo(x_origem, self.rect.bottom, 0, self.velocidade_projetil)
                        lista_tijolos.append(t)
                        
            return lista_tijolos
        return []

class Tijolo(pygame.sprite.Sprite):
    def __init__(self, x, y, vel_x, vel_y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(MARROM)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        self.velocidade_x = vel_x
        self.velocidade_y = vel_y

    def update(self):
        self.rect.x += self.velocidade_x
        self.rect.y += self.velocidade_y
        if (self.rect.top > ALTURA_TELA or self.rect.right < 0 or self.rect.left > LARGURA_TELA):
            self.kill()

class Urubu(pygame.sprite.Sprite):
    def __init__(self, nivel_atual):
        super().__init__()
        self.image = pygame.Surface((30, 20)) 
        self.image.fill((50, 50, 50)) 
        self.rect = self.image.get_rect()
        lado = random.choice([0, 1])
        andar_alvo = random.randint(1, 4)
        self.rect.y = ROWS_Y[andar_alvo] - 20 
        
        velocidade_base = 3
        velocidade_calculada = velocidade_base + (nivel_atual - 3) * 0.5
        
        if lado == 0: 
            self.rect.x = -30
            self.velocidade_x = velocidade_calculada
        else: 
            self.rect.x = LARGURA_TELA + 30
            self.velocidade_x = -velocidade_calculada
            
    def update(self):
        self.rect.x += self.velocidade_x
        if self.rect.right < -50 or self.rect.left > LARGURA_TELA + 50:
            self.kill()

class Janela(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo="quebrada"):
        super().__init__()
        self.tipo = tipo
        self.image = pygame.Surface((40, 40))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        if self.tipo == "fechada":
            self.image.fill(AZUL_ESCURO)
            self.hits_restantes = 0
            self.quebrada = False
        else:
            self.image.fill(AMARELO)
            self.hits_restantes = 2
            self.quebrada = True
    
    def consertar(self):
        if self.tipo == "quebrada" and self.quebrada:
            self.hits_restantes -= 1
            if self.hits_restantes == 1:
                self.image.fill(LARANJA)
                return False
            elif self.hits_restantes <= 0:
                self.hits_restantes = 0
                self.quebrada = False
                self.image.fill(VERDE)
                return True
        return False

class Plataforma(pygame.sprite.Sprite):
    def __init__(self, x, y, largura):
        super().__init__()
        self.image = pygame.Surface((largura, 10)) 
        self.image.fill(CINZA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# --- 3. SISTEMA DE HIGHSCORES ---

def carregar_highscores():
    if not os.path.exists(ARQUIVO_SCORES):
        return {"FACIL": [], "MEDIO": [], "DIFICIL": [], "DIFICILIMO": []}
    try:
        with open(ARQUIVO_SCORES, "r") as f:
            return json.load(f)
    except:
        return {"FACIL": [], "MEDIO": [], "DIFICIL": [], "DIFICILIMO": []}

def salvar_highscores(scores):
    try:
        with open(ARQUIVO_SCORES, "w") as f:
            json.dump(scores, f)
    except Exception as e:
        print(f"Erro ao salvar: {e}")

def atualizar_highscore(dificuldade, pontuacao):
    scores = carregar_highscores()
    lista = scores.get(dificuldade, [])
    lista.append(pontuacao)
    lista.sort(reverse=True)
    lista = lista[:10]
    scores[dificuldade] = lista
    salvar_highscores(scores)
    return lista

def desenhar_tela_fim_de_jogo(mensagem, cor, pontuacao_final, dificuldade_nome, ganhou=False):
    tela.fill(PRETO)
    
    texto_msg = fonte.render(mensagem, True, cor)
    rect_msg = texto_msg.get_rect(center=(LARGURA_TELA//2, 100))
    tela.blit(texto_msg, rect_msg)
    
    txt_pontos = fonte.render(f"SUA PONTUAÇÃO: {pontuacao_final}", True, BRANCO)
    rect_pontos = txt_pontos.get_rect(center=(LARGURA_TELA//2, 160))
    tela.blit(txt_pontos, rect_pontos)
    
    top_10 = atualizar_highscore(dificuldade_nome, pontuacao_final)
    
    txt_hs = fonte.render(f"TOP 10 - {dificuldade_nome}", True, DOURADO)
    tela.blit(txt_hs, (LARGURA_TELA//2 - 150, 220))
    
    fonte_pequena = pygame.font.SysFont("Arial", 30)
    for i, score in enumerate(top_10):
        cor_score = DOURADO if score == pontuacao_final else BRANCO
        txt = fonte_pequena.render(f"{i+1}. {score}", True, cor_score)
        tela.blit(txt, (LARGURA_TELA//2 - 100, 270 + (i * 35)))
        
    txt_sair = fonte_pequena.render("Pressione ESPAÇO para sair", True, CINZA)
    tela.blit(txt_sair, (LARGURA_TELA//2 - 150, 650))
    
    pygame.display.flip()
    
    esperando = True
    while esperando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    esperando = False

# --- 4. FUNÇÕES DE MENU E CENÁRIO ---

def mostrar_menu_dificuldade():
    menu_ativo = True
    config_escolhida = (4, "FACIL", False)
    input_codigo = ""
    debug_ativado = False
    
    while menu_ativo:
        tela.fill(PRETO)
        if debug_ativado:
            txt_debug = fonte.render("MODO DEBUG: ON", True, VERDE)
            tela.blit(txt_debug, (LARGURA_TELA - 350, 10))
            
        titulo = fonte.render("ESCOLHA A DIFICULDADE", True, AMARELO)
        rect_titulo = titulo.get_rect(center=(LARGURA_TELA//2, 150))
        tela.blit(titulo, rect_titulo)
        
        opcoes = [
            "1 - Fácil (4 Níveis)",
            "2 - Médio (8 Níveis)",
            "3 - Difícil (12 Níveis)",
            "4 - Dificílimo (16 Níveis + Ataque Especial)"
        ]
        
        for i, texto_opcao in enumerate(opcoes):
            texto = fonte.render(texto_opcao, True, (255, 255, 255))
            rect = texto.get_rect(center=(LARGURA_TELA//2, 300 + (i * 80)))
            tela.blit(texto, rect)
            
        if not debug_ativado:
            dica = pygame.font.SysFont("Arial", 20).render("(Digite o código secreto para debug)", True, (50, 50, 50))
            tela.blit(dica, (10, ALTURA_TELA - 30))
        
        pygame.display.flip()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.unicode.isalpha():
                    input_codigo += evento.unicode.lower()
                    input_codigo = input_codigo[-8:] 
                    if input_codigo == "quentalb":
                        debug_ativado = True
                        input_codigo = ""

                if evento.key == pygame.K_1: return (4, "FACIL", debug_ativado)
                if evento.key == pygame.K_2: return (8, "MEDIO", debug_ativado)
                if evento.key == pygame.K_3: return (12, "DIFICIL", debug_ativado)
                if evento.key == pygame.K_4: return (16, "DIFICILIMO", debug_ativado)
    return config_escolhida

def mostrar_menu_modo():
    menu_ativo = True
    while menu_ativo:
        tela.fill(PRETO)
        titulo = fonte.render("MODO DE JOGO", True, AMARELO)
        rect_titulo = titulo.get_rect(center=(LARGURA_TELA//2, 200))
        tela.blit(titulo, rect_titulo)
        
        texto1 = fonte.render("1 - Modo Pulo Livre", True, (255, 255, 255))
        rect1 = texto1.get_rect(center=(LARGURA_TELA//2, 350))
        tela.blit(texto1, rect1)
        
        texto2 = fonte.render("2 - Modo Clássico", True, (255, 255, 255))
        rect2 = texto2.get_rect(center=(LARGURA_TELA//2, 450))
        tela.blit(texto2, rect2)
        
        pygame.display.flip()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1: return "LIVRE"
                if evento.key == pygame.K_2: return "CLASSICO"
    return "CLASSICO"

def criar_cenario():
    for sprite in janelas: sprite.kill()
    for sprite in plataformas: sprite.kill()
    pos_y_inicial = 100        
    espaco_entre_andares = 115 
    largura_janela = 40
    for andar_idx in range(5):
        y = pos_y_inicial + (andar_idx * espaco_entre_andares)
        eh_andar_topo = (andar_idx == 0)
        if eh_andar_topo:
            x_inicio = COLS_X[0]
            x_fim = COLS_X[-1] + largura_janela
            largura_total = x_fim - x_inicio
            super_plataforma = Plataforma(x_inicio, y + 40, largura_total)
            todos_sprites.add(super_plataforma) 
            for x in COLS_X:
                janela_fechada = Janela(x, y, tipo="fechada")
                todos_sprites.add(janela_fechada)
                janelas.add(janela_fechada)
        else:
            for x in COLS_X:
                nova_janela = Janela(x, y, tipo="quebrada")
                todos_sprites.add(nova_janela)
                janelas.add(nova_janela)
                nova_plataforma = Plataforma(x, y + 40, largura_janela)
                todos_sprites.add(nova_plataforma)
                plataformas.add(nova_plataforma)

def transicao_fase():
    velocidade_scroll = 5
    altura_scroll = 0
    while altura_scroll < ALTURA_TELA:
        tela.fill(PRETO)
        for sprite in janelas: sprite.rect.y += velocidade_scroll
        for sprite in plataformas: sprite.rect.y += velocidade_scroll
        for sprite in itens_bonus: sprite.rect.y += velocidade_scroll
        
        todos_sprites.draw(tela)
        texto = fonte.render("PRÓXIMO NÍVEL!", True, (255, 255, 255))
        rect_texto = texto.get_rect(center=(LARGURA_TELA//2, ALTURA_TELA//2))
        tela.blit(texto, rect_texto)
        pygame.display.flip()
        altura_scroll += velocidade_scroll
        pygame.time.delay(10)

# --- 5. INICIALIZAÇÃO E LOOP PRINCIPAL ---

pygame.init()
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption(TITULO)
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("Arial", 40, bold=True)

# Grupos
todos_sprites = pygame.sprite.Group()
janelas = pygame.sprite.Group()
plataformas = pygame.sprite.Group()
tijolos = pygame.sprite.Group()
perigos = pygame.sprite.Group()
inimigos = pygame.sprite.Group()
itens_bonus = pygame.sprite.Group()

# Menus
max_niveis, nome_dificuldade, modo_debug_ativo = mostrar_menu_dificuldade()
modo_escolhido = mostrar_menu_modo()

# Setup Inicial
criar_cenario()
nivel_atual = 1
tempo_inicio_nivel = pygame.time.get_ticks()

jogador = Heroi(modo_escolhido, debug=modo_debug_ativo)
todos_sprites.add(jogador)

vilao = Inimigo()
vilao.atualizar_dificuldade(nivel_atual, max_niveis, nome_dificuldade)
todos_sprites.add(vilao)
inimigos.add(vilao)

# --- LOOP PRINCIPAL ---
rodando = True
while rodando:
    # Tempo
    tempo_decorrido = (pygame.time.get_ticks() - tempo_inicio_nivel) / 1000
    tempo_restante = TEMPO_LIMITE_NIVEL - tempo_decorrido
    
    # Verifica Tempo Esgotado
    if tempo_restante <= 0:
        desenhar_tela_fim_de_jogo("TEMPO ESGOTADO!", VERMELHO, jogador.pontuacao, nome_dificuldade)
        rodando = False

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_c:
                agora = pygame.time.get_ticks()
                if agora - jogador.ultimo_conserto > jogador.cooldown_conserto:
                    jogador.ultimo_conserto = agora
                    colisoes = pygame.sprite.spritecollide(jogador, janelas, False)
                    for janela in colisoes:
                        foi_consertada = janela.consertar()
                        if foi_consertada:
                            jogador.pontuacao += 100
                            jogador.contagem_consertos += 1
                            if jogador.contagem_consertos % 5 == 0:
                                janelas_disponiveis = [j for j in janelas if j.quebrada]
                                if janelas_disponiveis:
                                    j_alvo = random.choice(janelas_disponiveis)
                                    novo_item = ItemBonus(j_alvo.rect.centerx, j_alvo.rect.centery)
                                    todos_sprites.add(novo_item)
                                    itens_bonus.add(novo_item)

            if jogador.modo == "LIVRE":
                if evento.key == pygame.K_SPACE: jogador.pular_livre()
            elif jogador.modo == "CLASSICO":
                if evento.key == pygame.K_LEFT:  jogador.mover_classico(-1, 0)
                if evento.key == pygame.K_RIGHT: jogador.mover_classico(1, 0)
                if evento.key == pygame.K_UP:    jogador.mover_classico(0, -1)
                if evento.key == pygame.K_DOWN:  jogador.mover_classico(0, 1)

    todos_sprites.update()

    lista_de_tiros = vilao.tentar_atirar()
    for projetil in lista_de_tiros:
        todos_sprites.add(projetil)
        tijolos.add(projetil)
        perigos.add(projetil)

    if nivel_atual >= 3:
        chance_urubu = 0.5 + (nivel_atual * 0.2)
        if random.random() * 100 < chance_urubu:
            novo_urubu = Urubu(nivel_atual)
            todos_sprites.add(novo_urubu)
            perigos.add(novo_urubu)

    hits_itens = pygame.sprite.spritecollide(jogador, itens_bonus, True)
    for item in hits_itens:
        jogador.pontuacao += 300
        jogador.itens_coletados += 1
        if jogador.itens_coletados % 3 == 0:
            jogador.ativar_invencibilidade(6000)

    hits = pygame.sprite.spritecollide(jogador, perigos, False)
    for ameaca in hits:
        if jogador.tomar_dano():
            ameaca.kill()
            if jogador.vidas > 0:
                pass 

    # Game Over por Vidas
    if jogador.vidas <= 0:
        desenhar_tela_fim_de_jogo("GAME OVER", VERMELHO, jogador.pontuacao, nome_dificuldade)
        rodando = False

    tela.fill(PRETO)
    
    debug_status = " [DEBUG]" if jogador.modo_debug else ""
    status_invencivel = " [INVENCIVEL]" if jogador.invencivel and not jogador.modo_debug else ""
    
    info_texto = f"Vidas: {jogador.vidas} | Pts: {jogador.pontuacao} | Nível: {nivel_atual}/{max_niveis} | Tempo: {int(tempo_restante)}s"
    texto_hud = fonte.render(info_texto, True, (255, 255, 255))
    tela.blit(texto_hud, (10, 10))
    
    todos_sprites.draw(tela)
    pygame.display.flip()

    janelas_quebradas = [j for j in janelas if j.quebrada]
    if len(janelas_quebradas) == 0:
        
        bonus_vidas = jogador.vidas * 500
        bonus_tempo = int(tempo_restante) * 10
        jogador.pontuacao += bonus_vidas + bonus_tempo
        
        if nivel_atual >= max_niveis:
            desenhar_tela_fim_de_jogo("VOCÊ ZEROU O JOGO!", VERDE, jogador.pontuacao, nome_dificuldade, ganhou=True)
            rodando = False
        else:
            for ameaca in perigos: ameaca.kill()
            for item in itens_bonus: item.kill()
            
            jogador.rect.y = 90
            jogador.rect.x = LARGURA_TELA // 2
            pygame.display.flip()
            pygame.time.wait(1000)
            transicao_fase()
            criar_cenario()
            
            todos_sprites.remove(jogador); todos_sprites.add(jogador)
            todos_sprites.remove(vilao); todos_sprites.add(vilao)
            
            jogador.resetar_posicao()
            jogador.itens_coletados = 0 # --- CORREÇÃO: Reseta contador de itens ao passar de nível ---
            
            nivel_atual += 1
            vilao.atualizar_dificuldade(nivel_atual, max_niveis, nome_dificuldade)
            
            tempo_inicio_nivel = pygame.time.get_ticks() 

    relogio.tick(FPS)

pygame.quit()
sys.exit()