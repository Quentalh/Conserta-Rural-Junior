# sprites.py
import pygame
import random
import math
import os
from config import *
from utils import carregar_imagem

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
            self.rect.centerx = COLS_X[self.coluna_atual] + offset_centro
            self.rect.bottom = ROWS_Y[self.andar_atual] + offset_chao
        else:
            self.rect.centerx = COLS_X[2] + offset_centro
            self.rect.bottom = ROWS_Y[4] + offset_chao
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
        if self.modo_debug or self.invencivel: return False
        self.vidas -= 1
        if self.vidas > 0: self.ativar_invencibilidade(2000, tipo="DANO")
        return True 

    def atualizar_sprite(self):
        if self.modo_debug: return
        agora = pygame.time.get_ticks()
        if self.invencivel and self.tipo_invencibilidade == "DANO" and (agora - self.tempo_invencivel < 500):
            self.image = self.sprites['dano']
            return
        if self.esta_consertando:
            if agora < self.tempo_conserto_fim:
                self.image = self.sprites['bate_dir'] if self.olhando_direita else self.sprites['bate_esq']
                return
            else: self.esta_consertando = False 

        moveu = False
        if self.modo == "LIVRE":
            if self.velocidade_x > 0: self.olhando_direita = True; moveu = True
            elif self.velocidade_x < 0: self.olhando_direita = False; moveu = True
            esta_pulando = not self.no_chao
        else: 
            esta_pulando = self.pulando_classico
            moveu = self.pulando_classico 

        if esta_pulando:
            self.image = self.sprites['pulo_dir'] if self.olhando_direita else self.sprites['pulo_esq']
        elif moveu:
            if agora - self.timer_animacao > self.velocidade_animacao:
                self.timer_animacao = agora
                self.frame_index = (self.frame_index + 1) % 2 
            self.image = self.sprites['anda_dir'][self.frame_index] if self.olhando_direita else self.sprites['anda_esq'][self.frame_index]
        else:
            self.image = self.sprites['parado_dir'] if self.olhando_direita else self.sprites['parado_esq']

    def update(self):
        self.atualizar_sprite()
        if self.invencivel and not self.modo_debug:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_invencivel > self.duracao_invencibilidade_atual:
                self.invencivel = False
                self.image.set_alpha(255) 
            else:
                if self.tipo_invencibilidade == "DANO":
                    self.image.set_alpha(100 if (agora // 100) % 2 == 0 else 255)
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
        
        self.rect.x += self.velocidade_x
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > LARGURA_TELA: self.rect.right = LARGURA_TELA
        
        self.velocidade_y += self.gravidade
        self.rect.y += self.velocidade_y
        self.no_chao = False
        
        # Colisão com plataformas (importar main? Não, passar grupo ou importar em update)
        # NOTA: Para simplificar, assumimos que as colisões são tratadas no main.py
        # ou passamos as plataformas. O jeito mais fácil sem quebrar é manter a lógica básica
        # mas a colisão exata precisa do grupo 'plataformas'.
        # Para modularizar 100%, o update deveria receber as plataformas.
        pass # A lógica de colisão completa será movida para o main loop ou adaptada.

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
                self.rect.centerx = COLS_X[self.coluna_atual] + 50
                self.rect.bottom = ROWS_Y[self.andar_atual] + 100
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
            self.pulo_fim = (COLS_X[nc] + 50, ROWS_Y[na] + 100)

class Inimigo(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.largura = 120 
        self.altura = 120
        pasta_vilao = os.path.join("sprites", "vilao")
        img_v1 = carregar_imagem("vilao.png", self.largura, self.altura, VERMELHO, pasta=pasta_vilao)
        img_v2 = carregar_imagem("vilao2.png", self.largura, self.altura, VERMELHO, pasta=pasta_vilao)
        img_atk1 = carregar_imagem("vilao_soco.png", self.largura + 30, self.altura, VERMELHO, pasta=pasta_vilao)
        img_atk2 = carregar_imagem("vilao_soco2.png", self.largura + 30, self.altura, VERMELHO, pasta=pasta_vilao)
        img_golpe1 = carregar_imagem("vilao_golpe.png", self.largura + 30, self.altura, LARANJA, pasta=pasta_vilao)
        img_golpe2 = carregar_imagem("vilao_golpe2.png", self.largura + 30, self.altura, LARANJA, pasta=pasta_vilao)
        
        self.sprites = {
            'anda_dir': [img_v1, img_v2],
            'anda_esq': [pygame.transform.flip(img_v1, True, False), pygame.transform.flip(img_v2, True, False)],
            'atk_dir': [img_atk1, img_atk2],
            'atk_esq': [pygame.transform.flip(img_atk1, True, False), pygame.transform.flip(img_atk2, True, False)],
            'golpe_dir': [img_golpe1, img_golpe2],
            'golpe_esq': [pygame.transform.flip(img_golpe1, True, False), pygame.transform.flip(img_golpe2, True, False)]
        }
        self.image = self.sprites['anda_dir'][0]
        self.rect = self.image.get_rect()
        self.rect.centerx = COLS_X[2] + 50 
        self.rect.bottom = ROWS_Y[0] + 100
        
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
        if self.coluna_alvo_idx > 0: possibilidades.append(self.coluna_alvo_idx - 1)
        if self.coluna_alvo_idx < 4: possibilidades.append(self.coluna_alvo_idx + 1)
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
        if self.estado == "FURIA":
            self.image = self.sprites['golpe_dir'][self.frame_index] if self.olhando_direita else self.sprites['golpe_esq'][self.frame_index]
        elif self.esta_atacando or self.tijolos_pendentes > 0 or agora < self.pausa_pos_ataque:
            self.image = self.sprites['atk_dir'][self.frame_index] if self.olhando_direita else self.sprites['atk_esq'][self.frame_index]
        else:
            if self.chegou_no_alvo:
                self.image = self.sprites['anda_dir'][0] if self.olhando_direita else self.sprites['anda_esq'][0]
            else:
                self.image = self.sprites['anda_dir'][self.frame_index] if self.olhando_direita else self.sprites['anda_esq'][self.frame_index]

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
        elif self.estado == "FURIA": pass

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
                    if self.estado == "PATRULHA": self.escolher_proximo_alvo()
            return lista_tijolos
        if agora < self.pausa_pos_ataque: return []
        intervalo = self.intervalo_tiro_atual / 2.5 if self.estado == "FURIA" else self.intervalo_tiro_atual
        if agora - self.ultimo_tiro > intervalo:
            if self.estado == "PATRULHA":
                if self.chegou_no_alvo:
                    if random.random() < 0.5:
                        self.tijolos_pendentes = 3
                        self.tempo_ultimo_burst = agora - self.delay_burst
                    else: self.escolher_proximo_alvo()
            elif self.estado == "FURIA":
                self.ultimo_tiro = agora
                origens = [self.rect.centerx - 25, self.rect.centerx + 25]
                if self.tipo_ataque_especial == "LEQUE":
                    for x_origem in origens:
                        angulo_graus = random.uniform(-20, 20)
                        angulo_rad = math.radians(angulo_graus)
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
        self.sprites = {'dir': [img1, img2], 'esq': [pygame.transform.flip(img1, True, False), pygame.transform.flip(img2, True, False)]}
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
            self.image = self.sprites['dir'][self.frame_index] if self.velocidade_x > 0 else self.sprites['esq'][self.frame_index]
        if self.rect.right < -80 or self.rect.left > LARGURA_TELA + 80: self.kill()

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
        if self.tipo == "fechada": self.image.set_alpha(0) 
        else: self.atualizar_imagem() 
    def atualizar_imagem(self):
        if self.tipo == "fechada": return 
        if not self.quebrada: self.image = self.img_consertada
        else: self.image = self.img_quebrada if self.hits_restantes == 2 else self.img_meio
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
        if agora - self.tempo_nascimento > self.tempo_vida: self.kill()

class Plataforma(pygame.sprite.Sprite):
    def __init__(self, x, y, largura, visivel=True, cor=CINZA):
        super().__init__()
        self.image = pygame.Surface((largura, 15)) 
        self.image.fill(cor) 
        if not visivel: self.image.set_alpha(0)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y