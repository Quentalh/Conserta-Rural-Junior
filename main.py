import pygame
import sys
import random
import math
import json
import os

# --- 1. CONFIGURAÇÕES GLOBAIS ---
LARGURA_TELA = 1280
ALTURA_TELA = 1024 
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
MARROM_ESCURO = (92, 64, 51) 

# --- GRID AJUSTADO (Centralizado) ---
COLS_X = [150, 370, 590, 810, 1030]
ROWS_Y = [50, 200, 350, 500, 650] 

TEMPO_LIMITE_NIVEL = 70
ARQUIVO_SCORES = "highscores.json"

# --- FUNÇÕES AUXILIARES ---
def carregar_imagem(nome_arquivo, largura, altura, cor_fallback, pasta=""):
    caminho = os.path.join("assets", pasta, nome_arquivo)
    try:
        imagem = pygame.image.load(caminho).convert_alpha()
        imagem = pygame.transform.scale(imagem, (largura, altura))
        return imagem
    except Exception as e:
        print(f"AVISO: {nome_arquivo} não encontrado em '{caminho}'. Usando cor padrão. Erro: {e}")
        img_fallback = pygame.Surface((largura, altura))
        img_fallback.fill(cor_fallback)
        return img_fallback

# --- 2. CLASSES ---

class Heroi(pygame.sprite.Sprite):
    def __init__(self, modo_jogo, debug=False):
        super().__init__()
        self.modo = modo_jogo
        self.modo_debug = debug
        
        self.largura = 96
        self.altura = 96
        self.olhando_direita = True
        self.esta_consertando = False
        self.tempo_conserto_fim = 0
        
        self.frame_index = 0
        self.timer_animacao = 0
        self.velocidade_animacao = 150 
        
        if self.modo_debug:
            self.image = pygame.Surface((self.largura, self.altura))
            self.image.fill((0, 255, 255))
        else:
            pasta_heroi = os.path.join("sprites", "heroi")
            img_parado = carregar_imagem("heroi.png", self.largura, self.altura, AZUL, pasta=pasta_heroi)
            img_pulo1 = carregar_imagem("heroi_pulo.png", self.largura, self.altura, AZUL, pasta=pasta_heroi)
            img_pulo2 = carregar_imagem("heroi_pulo2.png", self.largura, self.altura, AZUL, pasta=pasta_heroi)
            img_bate = carregar_imagem("heroi_bate.png", self.largura + 30, self.altura, AZUL, pasta=pasta_heroi)
            img_dano = carregar_imagem("heroi_dano.png", self.largura, self.altura, VERMELHO, pasta=pasta_heroi)
            
            self.sprites = {
                'parado_dir': pygame.transform.flip(img_parado, True, False),
                'parado_esq': img_parado,
                'pulo_dir': pygame.transform.flip(img_pulo1, True, False),
                'pulo_esq': img_pulo1,
                'anda_dir': [pygame.transform.flip(img_pulo2, True, False), pygame.transform.flip(img_pulo1, True, False)],
                'anda_esq': [img_pulo2, img_pulo1],
                'bate_dir': img_bate,
                'bate_esq': pygame.transform.flip(img_bate, True, False),
                'dano': img_dano
            }
            self.image = self.sprites['parado_dir']
            
        self.rect = self.image.get_rect()
        self.vidas = 3
        self.pontuacao = 0
        self.contagem_consertos = 0 
        self.itens_coletados = 0    
        
        self.invencivel = False
        self.tempo_invencivel = 0
        self.duracao_invencibilidade_atual = 2000
        self.tipo_invencibilidade = "DANO"
        
        self.ultimo_conserto = 0
        self.cooldown_conserto = 400
        
        self.velocidade_x = 0
        self.velocidade_y = 0
        self.gravidade = 1.2
        self.forca_pulo = -22
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
        offset_centro = 50 
        offset_chao = 100
        
        if self.modo == "CLASSICO":
            self.coluna_atual = 2
            self.andar_atual = 4
            centro_janela_x = COLS_X[self.coluna_atual] + offset_centro
            self.rect.centerx = centro_janela_x
            chao_y = ROWS_Y[self.andar_atual] + offset_chao
            self.rect.bottom = chao_y
        else:
            centro_janela_x = COLS_X[2] + offset_centro
            chao_y = ROWS_Y[4] + offset_chao
            self.rect.centerx = centro_janela_x
            self.rect.bottom = chao_y
            self.velocidade_y = 0
            self.ultima_posicao_segura = (self.rect.centerx, self.rect.bottom)

    def ativar_invencibilidade(self, duracao, tipo="DANO"):
        self.invencivel = True
        self.tempo_invencivel = pygame.time.get_ticks()
        self.duracao_invencibilidade_atual = duracao
        self.tipo_invencibilidade = tipo 

    def iniciar_conserto(self):
        self.esta_consertando = True
        self.tempo_conserto_fim = pygame.time.get_ticks() + 300 

    def tomar_dano(self):
        if self.modo_debug or self.invencivel:
            return False
        self.vidas -= 1
        if self.vidas > 0:
            self.ativar_invencibilidade(2000, tipo="DANO")
        return True 

    def atualizar_sprite(self):
        if self.modo_debug: return
        agora = pygame.time.get_ticks()

        if self.invencivel and self.tipo_invencibilidade == "DANO" and (agora - self.tempo_invencivel < 500):
            self.image = self.sprites['dano']
            return

        if self.esta_consertando:
            if agora < self.tempo_conserto_fim:
                if self.olhando_direita: self.image = self.sprites['bate_dir']
                else: self.image = self.sprites['bate_esq']
                return
            else:
                self.esta_consertando = False 

        moveu = False
        if self.modo == "LIVRE":
            if self.velocidade_x > 0: self.olhando_direita = True; moveu = True
            elif self.velocidade_x < 0: self.olhando_direita = False; moveu = True
            esta_pulando = not self.no_chao
        else: 
            esta_pulando = self.pulando_classico
            moveu = self.pulando_classico 

        if esta_pulando:
            if self.olhando_direita: self.image = self.sprites['pulo_dir']
            else: self.image = self.sprites['pulo_esq']
        elif moveu:
            if agora - self.timer_animacao > self.velocidade_animacao:
                self.timer_animacao = agora
                self.frame_index = (self.frame_index + 1) % 2 
            if self.olhando_direita: self.image = self.sprites['anda_dir'][self.frame_index]
            else: self.image = self.sprites['anda_esq'][self.frame_index]
        else:
            if self.olhando_direita: self.image = self.sprites['parado_dir']
            else: self.image = self.sprites['parado_esq']

    def update(self):
        self.atualizar_sprite()
        
        if self.invencivel and not self.modo_debug:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_invencivel > self.duracao_invencibilidade_atual:
                self.invencivel = False
                self.image.set_alpha(255) 
            else:
                if self.tipo_invencibilidade == "DANO":
                    if (agora // 100) % 2 == 0: self.image.set_alpha(100)
                    else: self.image.set_alpha(255)
                elif self.tipo_invencibilidade == "ITEM":
                    self.image.set_alpha(255) 
                    img_brilhante = self.image.copy()
                    brilho = pygame.Surface(img_brilhante.get_size(), pygame.SRCALPHA)
                    brilho.fill((255, 255, 0, 100))
                    img_brilhante.blit(brilho, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                    self.image = img_brilhante
        else:
            self.image.set_alpha(255)

        if self.modo == "LIVRE": self.update_livre()
        else: self.update_classico()

    def update_livre(self):
        self.velocidade_x = 0
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]: self.velocidade_x = -8
        if teclas[pygame.K_RIGHT]: self.velocidade_x = 8
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
                
                centro_janela_x = COLS_X[self.coluna_atual] + 50
                self.rect.centerx = centro_janela_x
                chao_y = ROWS_Y[self.andar_atual] + 100
                self.rect.bottom = chao_y
            else:
                ix, iy = self.pulo_inicio
                fx, fy = self.pulo_fim
                novo_x = ix + (fx - ix) * self.pulo_progresso
                arco = 75 * 4 * self.pulo_progresso * (1 - self.pulo_progresso)
                base_y = iy + (fy - iy) * self.pulo_progresso
                self.rect.centerx = int(novo_x)
                self.rect.bottom = int(base_y - arco)

    def mover_classico(self, dx, dy):
        if self.pulando_classico: return
        if dx > 0: self.olhando_direita = True
        if dx < 0: self.olhando_direita = False
        nc, na = self.coluna_atual + dx, self.andar_atual + dy
        if 0 <= nc < 5 and 1 <= na < 5:
            self.pulando_classico = True
            self.pulo_progresso = 0.0
            self.pulo_inicio = (self.rect.centerx, self.rect.bottom)
            self.coluna_atual, self.andar_atual = nc, na
            
            destino_x = COLS_X[nc] + 50
            destino_y = ROWS_Y[na] + 100
            self.pulo_fim = (destino_x, destino_y)

class ItemBonus(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        pasta_item = os.path.join("sprites", "item")
        self.image = carregar_imagem("cuscuz.png", 45, 45, DOURADO, pasta=pasta_item)
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
        self.largura = 120 
        self.altura = 120
        
        pasta_vilao = os.path.join("sprites", "vilao")
        # --- CARREGAMENTO DE TODOS OS SPRITES DO VILÃO ---
        img_v1 = carregar_imagem("vilao.png", self.largura, self.altura, VERMELHO, pasta=pasta_vilao)
        img_v2 = carregar_imagem("vilao2.png", self.largura, self.altura, VERMELHO, pasta=pasta_vilao)
        img_atk1 = carregar_imagem("vilao_soco.png", self.largura + 30, self.altura, VERMELHO, pasta=pasta_vilao)
        img_atk2 = carregar_imagem("vilao_soco2.png", self.largura + 30, self.altura, VERMELHO, pasta=pasta_vilao)
        
        # Novos sprites de Golpe Especial
        img_golpe1 = carregar_imagem("vilao_golpe.png", self.largura + 30, self.altura, LARANJA, pasta=pasta_vilao)
        img_golpe2 = carregar_imagem("vilao_golpe2.png", self.largura + 30, self.altura, LARANJA, pasta=pasta_vilao)
        
        self.sprites = {
            'anda_dir': [img_v1, img_v2],
            'anda_esq': [pygame.transform.flip(img_v1, True, False), pygame.transform.flip(img_v2, True, False)],
            'atk_dir': [img_atk1, img_atk2],
            'atk_esq': [pygame.transform.flip(img_atk1, True, False), pygame.transform.flip(img_atk2, True, False)],
            # Dicionário do Ataque Especial
            'golpe_dir': [img_golpe1, img_golpe2],
            'golpe_esq': [pygame.transform.flip(img_golpe1, True, False), pygame.transform.flip(img_golpe2, True, False)]
        }
        
        self.image = self.sprites['anda_dir'][0]
        self.rect = self.image.get_rect()
        
        # Ajuste para nova coordenada centralizada (+50px)
        self.rect.centerx = COLS_X[2] + 50 
        
        chao_plataforma_topo = ROWS_Y[0] + 100
        self.rect.bottom = chao_plataforma_topo
        
        self.frame_index = 0
        self.timer_animacao = 0
        self.velocidade_animacao = 200
        self.olhando_direita = True
        self.esta_atacando = False
        
        self.velocidade_base = 6
        self.velocidade = 6
        self.velocidade_projetil = 6
        self.coluna_alvo_idx = 2 
        self.chegou_no_alvo = True 
        
        self.estado = "PATRULHA"
        self.ultimo_troca_estado = pygame.time.get_ticks()
        self.tempo_para_proxima_troca = random.randint(3000, 6000)
        
        self.ultimo_tiro = 0
        self.intervalo_tiro_base = 600
        self.intervalo_tiro_atual = 600
        self.tempo_pausa_base = 2000 
        self.tempo_pausa_atual = 2000 
        
        self.pode_entrar_furia = False
        self.tipo_ataque_especial = "NENHUM"
        self.pausa_pos_ataque = 0 
        self.tijolos_pendentes = 0     
        self.tempo_ultimo_burst = 0    
        self.delay_burst = 200

    def atualizar_dificuldade(self, nivel, max_niveis, nome_dificuldade):
        self.velocidade = self.velocidade_base + (nivel * 0.8)
        novo_intervalo = self.intervalo_tiro_base - (nivel * 60)
        self.intervalo_tiro_atual = max(250, novo_intervalo)
        self.velocidade_projetil = 5 + (nivel * 0.8)
        self.tempo_pausa_atual = max(500, self.tempo_pausa_base - (nivel * 150))
        
        self.pode_entrar_furia = False
        self.tipo_ataque_especial = "NENHUM"
        niveis_para_fim = max_niveis - nivel + 1
        
        if nome_dificuldade == "DIFICILIMO" and niveis_para_fim <= 4:
            self.pode_entrar_furia = True
            self.tipo_ataque_especial = "LEQUE"
        elif nome_dificuldade == "DIFICIL" and niveis_para_fim <= 2:
            self.pode_entrar_furia = True
            self.tipo_ataque_especial = "METRALHADORA"

    def escolher_proximo_alvo(self):
        possibilidades = []
        if self.coluna_alvo_idx > 0:
            possibilidades.append(self.coluna_alvo_idx - 1)
        if self.coluna_alvo_idx < 4:
            possibilidades.append(self.coluna_alvo_idx + 1)
            
        if possibilidades:
            self.coluna_alvo_idx = random.choice(possibilidades)
            self.chegou_no_alvo = False 

    def atualizar_sprite(self):
        agora = pygame.time.get_ticks()
        
        x_destino = COLS_X[self.coluna_alvo_idx] + 50
        if not self.chegou_no_alvo:
            if x_destino > self.rect.centerx: self.olhando_direita = True
            else: self.olhando_direita = False
            
        if agora - self.timer_animacao > self.velocidade_animacao:
            self.timer_animacao = agora
            self.frame_index = (self.frame_index + 1) % 2

        # --- LÓGICA DE ANIMAÇÃO DE ATAQUE ESPECIAL (FÚRIA) ---
        if self.estado == "FURIA":
            if self.olhando_direita: self.image = self.sprites['golpe_dir'][self.frame_index]
            else: self.image = self.sprites['golpe_esq'][self.frame_index]
        # --- LÓGICA DE ANIMAÇÃO DE ATAQUE NORMAL ---
        elif self.esta_atacando or self.tijolos_pendentes > 0 or agora < self.pausa_pos_ataque:
            if self.olhando_direita: self.image = self.sprites['atk_dir'][self.frame_index]
            else: self.image = self.sprites['atk_esq'][self.frame_index]
        # --- LÓGICA DE MOVIMENTO NORMAL ---
        else:
            if self.chegou_no_alvo:
                if self.olhando_direita: self.image = self.sprites['anda_dir'][0]
                else: self.image = self.sprites['anda_esq'][0]
            else:
                if self.olhando_direita: self.image = self.sprites['anda_dir'][self.frame_index]
                else: self.image = self.sprites['anda_esq'][self.frame_index]

    def update(self):
        self.atualizar_sprite()
        agora = pygame.time.get_ticks()
        
        if self.tijolos_pendentes > 0 or agora < self.pausa_pos_ataque:
            self.esta_atacando = True
            return 
        
        self.esta_atacando = False

        if self.pode_entrar_furia:
            if agora - self.ultimo_troca_estado > self.tempo_para_proxima_troca:
                self.ultimo_troca_estado = agora
                if self.estado == "PATRULHA":
                    self.estado = "FURIA"
                    self.tempo_para_proxima_troca = random.randint(2000, 4000)
                else:
                    self.estado = "PATRULHA"
                    self.chegou_no_alvo = False 
                    self.tempo_para_proxima_troca = random.randint(3000, 6000)

        if self.estado == "PATRULHA":
            x_destino = COLS_X[self.coluna_alvo_idx] + 50
            distancia = x_destino - self.rect.centerx
            
            if abs(distancia) <= self.velocidade:
                self.rect.centerx = x_destino
                self.chegou_no_alvo = True
            else:
                direcao = 1 if distancia > 0 else -1
                self.rect.centerx += direcao * self.velocidade
                self.chegou_no_alvo = False
                
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
                    self.pausa_pos_ataque = agora + self.tempo_pausa_atual
                    self.ultimo_tiro = agora
                    if self.estado == "PATRULHA":
                        self.escolher_proximo_alvo()
            return lista_tijolos

        if agora < self.pausa_pos_ataque:
            return []
            
        if self.estado == "FURIA":
            intervalo = self.intervalo_tiro_atual / 2.5 
        else:
            intervalo = self.intervalo_tiro_atual

        if agora - self.ultimo_tiro > intervalo:
            if self.estado == "PATRULHA":
                if self.chegou_no_alvo:
                    if random.random() < 0.5:
                        self.tijolos_pendentes = 3
                        self.tempo_ultimo_burst = agora - self.delay_burst
                    else:
                        self.escolher_proximo_alvo()

            elif self.estado == "FURIA":
                self.ultimo_tiro = agora
                origens = [self.rect.centerx - 25, self.rect.centerx + 25]
                if self.tipo_ataque_especial == "LEQUE":
                    for x_origem in origens:
                        # --- ATAQUE ESPECIAL: Leque Menor e Mais Lento ---
                        angulo_graus = random.uniform(-20, 20) # Reduzido de 35 para 20
                        angulo_rad = math.radians(angulo_graus)
                        
                        # Velocidade reduzida em 30% para ser "desviável"
                        velocidade_reduzida = self.velocidade_projetil * 0.7 
                        
                        vx = velocidade_reduzida * math.sin(angulo_rad)
                        vy = velocidade_reduzida * math.cos(angulo_rad)
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
        pasta_tijolo = os.path.join("sprites", "tijolo")
        self.image = carregar_imagem("tijolo.png", 64, 32, MARROM, pasta=pasta_tijolo)
        
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
        self.largura = 60
        self.altura = 45
        
        pasta_urubu = os.path.join("sprites", "urubu")
        img1 = carregar_imagem("passaro.png", self.largura, self.altura, CINZA, pasta=pasta_urubu)
        img2 = carregar_imagem("passaro2.png", self.largura, self.altura, CINZA, pasta=pasta_urubu)
        
        self.sprites = {
            'dir': [img1, img2],
            'esq': [pygame.transform.flip(img1, True, False), pygame.transform.flip(img2, True, False)]
        }
        
        self.image = self.sprites['dir'][0]
        self.rect = self.image.get_rect()
        
        lado = random.choice([0, 1])
        andar_alvo = random.randint(1, 4)
        self.rect.y = ROWS_Y[andar_alvo] - 20 
        
        velocidade_base = 4.5 
        velocidade_calculada = velocidade_base + (nivel_atual - 3) * 0.7
        
        if lado == 0: 
            self.rect.x = -60
            self.velocidade_x = velocidade_calculada
        else: 
            self.rect.x = LARGURA_TELA + 60
            self.velocidade_x = -velocidade_calculada
            
        self.frame_index = 0
        self.timer_animacao = 0
        self.velocidade_animacao = 100

    def update(self):
        self.rect.x += self.velocidade_x
        
        agora = pygame.time.get_ticks()
        if agora - self.timer_animacao > self.velocidade_animacao:
            self.timer_animacao = agora
            self.frame_index = (self.frame_index + 1) % 2
            
            if self.velocidade_x > 0:
                self.image = self.sprites['dir'][self.frame_index]
            else:
                self.image = self.sprites['esq'][self.frame_index]

        if self.rect.right < -80 or self.rect.left > LARGURA_TELA + 80:
            self.kill()

class Janela(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo="quebrada"):
        super().__init__()
        self.tipo = tipo
        self.hits_restantes = 0 if tipo == "fechada" else 2
        self.quebrada = (tipo == "quebrada")
        
        self.largura_j = 100
        self.altura_j = 100
        
        pasta_janela = os.path.join("sprites", "janela")
        self.img_quebrada = carregar_imagem("janela_quebrada.png", self.largura_j, self.altura_j, AMARELO, pasta=pasta_janela)
        self.img_meio = carregar_imagem("janela_meio_consertada.png", self.largura_j, self.altura_j, LARANJA, pasta=pasta_janela)
        self.img_consertada = carregar_imagem("janela_consertada.png", self.largura_j, self.altura_j, AZUL_ESCURO, pasta=pasta_janela)
        
        self.image = self.img_quebrada 
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        if self.tipo == "fechada":
            self.image.set_alpha(0) 
        else:
            self.atualizar_imagem() 

    def atualizar_imagem(self):
        if self.tipo == "fechada": return 
        
        if not self.quebrada:
            self.image = self.img_consertada
        else:
            if self.hits_restantes == 2:
                self.image = self.img_quebrada
            elif self.hits_restantes == 1:
                self.image = self.img_meio

    def consertar(self):
        if self.tipo == "quebrada" and self.quebrada:
            self.hits_restantes -= 1
            
            if self.hits_restantes <= 0:
                self.hits_restantes = 0
                self.quebrada = False
                self.atualizar_imagem()
                return True 
            else:
                self.atualizar_imagem()
                return False 
        return False

class Plataforma(pygame.sprite.Sprite):
    def __init__(self, x, y, largura, visivel=True, cor=CINZA):
        super().__init__()
        self.image = pygame.Surface((largura, 15)) 
        self.image.fill(cor) 
        
        if not visivel:
            self.image.set_alpha(0)
            
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
    if ganhou:
        tela.blit(img_tela_vitoria, (0, 0))
    else:
        tela.blit(img_tela_gameover, (0, 0))
    
    caixa = pygame.Surface((600, 500))
    caixa.set_alpha(180)
    caixa.fill(PRETO)
    tela.blit(caixa, (LARGURA_TELA//2 - 300, 80))

    texto_msg = fonte.render(mensagem, True, cor)
    rect_msg = texto_msg.get_rect(center=(LARGURA_TELA//2, 120))
    tela.blit(texto_msg, rect_msg)
    
    txt_pontos = fonte.render(f"SUA PONTUAÇÃO: {pontuacao_final}", True, BRANCO)
    rect_pontos = txt_pontos.get_rect(center=(LARGURA_TELA//2, 180))
    tela.blit(txt_pontos, rect_pontos)
    
    top_10 = atualizar_highscore(dificuldade_nome, pontuacao_final)
    
    txt_hs = fonte.render(f"TOP 10 - {dificuldade_nome}", True, DOURADO)
    tela.blit(txt_hs, (LARGURA_TELA//2 - 150, 240))
    
    fonte_pequena = pygame.font.SysFont("Arial", 30)
    for i, score in enumerate(top_10):
        if i > 7: break 
        cor_score = DOURADO if score == pontuacao_final else BRANCO
        txt = fonte_pequena.render(f"{i+1}. {score}", True, cor_score)
        tela.blit(txt, (LARGURA_TELA//2 - 100, 290 + (i * 30)))
        
    txt_sair = fonte_pequena.render("Pressione ESPAÇO para Voltar ao Menu", True, CINZA)
    tela.blit(txt_sair, (LARGURA_TELA//2 - 200, 540))
    
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
    pygame.event.clear()
    menu_ativo = True
    config_escolhida = (4, "FACIL", False)
    input_codigo = ""
    debug_ativado = False
    
    bg_menu = carregar_imagem("menu_dificuldade.png", LARGURA_TELA, ALTURA_TELA, PRETO, pasta="menu")
    
    while menu_ativo:
        tela.blit(bg_menu, (0, 0))
        
        if debug_ativado:
            txt_debug = fonte.render("MODO DEBUG: ON", True, VERDE)
            tela.blit(txt_debug, (LARGURA_TELA - 350, 10))
            
        sombra_titulo = pygame.Surface((500, 60))
        sombra_titulo.set_alpha(150)
        sombra_titulo.fill(PRETO)
        rect_sombra = sombra_titulo.get_rect(center=(LARGURA_TELA//2, 150))
        tela.blit(sombra_titulo, rect_sombra)

        titulo = fonte.render("ESCOLHA A DIFICULDADE", True, AMARELO)
        rect_titulo = titulo.get_rect(center=(LARGURA_TELA//2, 150))
        tela.blit(titulo, rect_titulo)
        
        opcoes = [
            "1 - Fácil (4 Níveis)",
            "2 - Médio (6 Níveis)", 
            "3 - Difícil (8 Níveis)",
            "4 - Dificílimo (10 Níveis + Ataque Especial)",
            "5 - Sair do Jogo"
        ]
        
        for i, texto_opcao in enumerate(opcoes):
            cor = VERMELHO if i == 4 else BRANCO
            texto = fonte.render(texto_opcao, True, cor)
            
            texto_sombra = fonte.render(texto_opcao, True, PRETO)
            rect = texto.get_rect(center=(LARGURA_TELA//2, 300 + (i * 60)))
            
            tela.blit(texto_sombra, (rect.x + 2, rect.y + 2))
            tela.blit(texto, rect)
            
        if not debug_ativado:
            dica = pygame.font.SysFont("Arial", 20).render("(Digite o código secreto para debug)", True, (255, 255, 255))
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
                if evento.key == pygame.K_2: return (6, "MEDIO", debug_ativado)
                if evento.key == pygame.K_3: return (8, "DIFICIL", debug_ativado)
                if evento.key == pygame.K_4: return (10, "DIFICILIMO", debug_ativado)
                if evento.key == pygame.K_5 or evento.key == pygame.K_ESCAPE: return None 
    return config_escolhida

def mostrar_menu_modo():
    pygame.event.clear()
    menu_ativo = True
    
    bg_menu = carregar_imagem("menu_dificuldade.png", LARGURA_TELA, ALTURA_TELA, PRETO, pasta="menu")
    
    while menu_ativo:
        tela.blit(bg_menu, (0, 0))
        
        caixa = pygame.Surface((600, 400))
        caixa.set_alpha(180)
        caixa.fill(PRETO)
        tela.blit(caixa, (LARGURA_TELA//2 - 300, 150))
        
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
    
    largura_janela = 100 
    
    for andar_idx in range(5):
        y = ROWS_Y[andar_idx]
        eh_andar_topo = (andar_idx == 0)
        
        if eh_andar_topo:
            x_inicio = COLS_X[0]
            x_fim = COLS_X[-1] + largura_janela
            largura_total = x_fim - x_inicio
            
            # Plataforma topo (Vilão) -> VISÍVEL e LARANJA
            super_plataforma = Plataforma(x_inicio, y + 100, largura_total, visivel=True, cor=MARROM_ESCURO)
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
                
                # Plataformas de baixo -> INVISÍVEIS
                nova_plataforma = Plataforma(x, y + 100, largura_janela, visivel=False)
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

# Carregamento dos Cenários e Assets Gráficos
img_predio_inicio = carregar_imagem("ceagri_inicio.png", LARGURA_TELA, ALTURA_TELA, CINZA, pasta="predio")
img_predio_meio = carregar_imagem("ceagri_meio.png", LARGURA_TELA, ALTURA_TELA, CINZA, pasta="predio")
img_predio_topo = carregar_imagem("ceagri_topo.png", LARGURA_TELA, ALTURA_TELA, CINZA, pasta="predio")

img_tela_vitoria = carregar_imagem("tela_vitoria.png", LARGURA_TELA, ALTURA_TELA, VERDE, pasta="telas")
img_tela_gameover = carregar_imagem("tela_gameover.png", LARGURA_TELA, ALTURA_TELA, VERMELHO, pasta="telas")
img_vida = carregar_imagem("vida.png", 40, 40, VERMELHO, pasta="vidas")

# --- LOOP DA APLICAÇÃO ---
aplicacao_rodando = True

while aplicacao_rodando:
    # 1. MOSTRAR MENUS
    resultado_menu = mostrar_menu_dificuldade()
    
    if resultado_menu is None:
        aplicacao_rodando = False
        break
        
    max_niveis, nome_dificuldade, modo_debug_ativo = resultado_menu
    modo_escolhido = mostrar_menu_modo()

    # 2. RESETAR E INICIAR O JOGO
    todos_sprites.empty()
    janelas.empty()
    plataformas.empty()
    tijolos.empty()
    perigos.empty()
    inimigos.empty()
    itens_bonus.empty()

    criar_cenario()
    nivel_atual = 1
    tempo_inicio_nivel = pygame.time.get_ticks()

    jogador = Heroi(modo_escolhido, debug=modo_debug_ativo)
    todos_sprites.add(jogador)

    vilao = Inimigo()
    vilao.atualizar_dificuldade(nivel_atual, max_niveis, nome_dificuldade)
    todos_sprites.add(vilao)
    inimigos.add(vilao)

    # 3. LOOP DO JOGO (PARTIDA ATUAL)
    jogo_rodando = True
    while jogo_rodando:
        tempo_decorrido = (pygame.time.get_ticks() - tempo_inicio_nivel) / 1000
        tempo_restante = TEMPO_LIMITE_NIVEL - tempo_decorrido
        
        if tempo_restante <= 0:
            desenhar_tela_fim_de_jogo("TEMPO ESGOTADO!", VERMELHO, jogador.pontuacao, nome_dificuldade)
            jogo_rodando = False

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                jogo_rodando = False; aplicacao_rodando = False
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE: jogo_rodando = False

                if evento.key == pygame.K_c:
                    agora = pygame.time.get_ticks()
                    if agora - jogador.ultimo_conserto > jogador.cooldown_conserto:
                        colisoes = pygame.sprite.spritecollide(jogador, janelas, False)
                        fez_algum_conserto = False
                        for janela in colisoes:
                            if janela.quebrada:
                                jogador.ultimo_conserto = agora
                                fez_algum_conserto = True
                                foi_totalmente_consertada = janela.consertar()
                                jogador.pontuacao += 50 
                                if foi_totalmente_consertada:
                                    jogador.pontuacao += 50
                                    jogador.contagem_consertos += 1
                                    if jogador.contagem_consertos % 5 == 0:
                                        janelas_disponiveis = [j for j in janelas if j.quebrada]
                                        if janelas_disponiveis:
                                            j_alvo = random.choice(janelas_disponiveis)
                                            novo_item = ItemBonus(j_alvo.rect.centerx, j_alvo.rect.centery)
                                            todos_sprites.add(novo_item)
                                            itens_bonus.add(novo_item)
                        if fez_algum_conserto:
                            jogador.iniciar_conserto()

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
                jogador.ativar_invencibilidade(6000, tipo="ITEM")

        hits = pygame.sprite.spritecollide(jogador, perigos, False)
        for ameaca in hits:
            if jogador.tomar_dano():
                ameaca.kill()

        if jogador.vidas <= 0:
            desenhar_tela_fim_de_jogo("GAME OVER", VERMELHO, jogador.pontuacao, nome_dificuldade)
            jogo_rodando = False

        # --- DESENHO DA TELA ---
        if nivel_atual == 1:
            tela.blit(img_predio_inicio, (0, 0))
        elif nivel_atual == max_niveis:
            tela.blit(img_predio_topo, (0, 0))
        else:
            tela.blit(img_predio_meio, (0, 0))
            
        bg_hud = pygame.Surface((LARGURA_TELA, 50))
        bg_hud.set_alpha(150)
        bg_hud.fill(PRETO)
        tela.blit(bg_hud, (0,0))
        
        for i in range(jogador.vidas):
            tela.blit(img_vida, (10 + i * 45, 5))
        
        info_texto = f"Pts: {jogador.pontuacao} | Nível: {nivel_atual}/{max_niveis} | Tempo: {int(tempo_restante)}s"
        texto_hud = fonte.render(info_texto, True, (255, 255, 255))
        tela.blit(texto_hud, (160, 5))
        
        todos_sprites.draw(tela)
        pygame.display.flip()

        # --- Lógica de Vitória de Nível ---
        janelas_quebradas = [j for j in janelas if j.quebrada]
        if len(janelas_quebradas) == 0:
            bonus_vidas = jogador.vidas * 500
            bonus_tempo = int(tempo_restante) * 10
            jogador.pontuacao += bonus_vidas + bonus_tempo
            
            if nivel_atual >= max_niveis:
                desenhar_tela_fim_de_jogo("VOCÊ ZEROU O JOGO!", VERDE, jogador.pontuacao, nome_dificuldade, ganhou=True)
                jogo_rodando = False 
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
                jogador.itens_coletados = 0 
                
                nivel_atual += 1
                vilao.atualizar_dificuldade(nivel_atual, max_niveis, nome_dificuldade)
                tempo_inicio_nivel = pygame.time.get_ticks() 

        relogio.tick(FPS)

pygame.quit()
sys.exit()