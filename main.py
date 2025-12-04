# main.py
import pygame
import sys
import random

# --- IMPORTAÇÃO DOS MÓDULOS ---
from config import *
from utils import carregar_imagem
# ADICIONADO: mostrar_tela_titulo na importação
from ui import mostrar_menu_dificuldade, mostrar_menu_modo, desenhar_tela_fim_de_jogo, mostrar_tela_titulo
from sprites import Heroi, Inimigo, Tijolo, Urubu, Janela, Plataforma, ItemBonus

# --- INICIALIZAÇÃO ---
pygame.init()
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption(TITULO)
relogio = pygame.time.Clock()

# Fonte para o HUD (Heads-Up Display)
fonte_hud = pygame.font.SysFont("Arial", 40, bold=True)

# --- GRUPOS DE SPRITES ---
todos_sprites = pygame.sprite.Group()
janelas = pygame.sprite.Group()
plataformas = pygame.sprite.Group()
tijolos = pygame.sprite.Group()
perigos = pygame.sprite.Group()
inimigos = pygame.sprite.Group()
itens_bonus = pygame.sprite.Group()

# --- CARREGAMENTO DE ASSETS GLOBAIS ---
img_predio_inicio = carregar_imagem("ceagri_inicio.png", LARGURA_TELA, ALTURA_TELA, CINZA, pasta="predio")
img_predio_meio = carregar_imagem("ceagri_meio.png", LARGURA_TELA, ALTURA_TELA, CINZA, pasta="predio")
img_predio_topo = carregar_imagem("ceagri_topo.png", LARGURA_TELA, ALTURA_TELA, CINZA, pasta="predio")
img_vida = carregar_imagem("vida.png", 40, 40, VERMELHO, pasta="vidas")

# --- FUNÇÕES LOCAIS ---

def criar_cenario():
    """Recria o cenário do prédio com plataformas e janelas."""
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
            
            # Plataforma topo (Vilão) -> VISÍVEL e MARROM ESCURO
            super_plataforma = Plataforma(x_inicio, y + 100, largura_total, visivel=True, cor=MARROM_ESCURO)
            todos_sprites.add(super_plataforma)
            
            # Janelas invisíveis do vilão (para manter a lógica do grid)
            for x in COLS_X:
                janela_fechada = Janela(x, y, tipo="fechada") 
                todos_sprites.add(janela_fechada)
                janelas.add(janela_fechada)
        else:
            # Andares jogáveis
            for x in COLS_X:
                nova_janela = Janela(x, y, tipo="quebrada")
                todos_sprites.add(nova_janela)
                janelas.add(nova_janela)
                
                # Plataformas de baixo -> INVISÍVEIS (para ver o background)
                nova_plataforma = Plataforma(x, y + 100, largura_janela, visivel=False)
                todos_sprites.add(nova_plataforma)
                plataformas.add(nova_plataforma)

def transicao_fase():
    """Animação simples de scroll vertical entre níveis."""
    velocidade_scroll = 5
    altura_scroll = 0
    
    while altura_scroll < ALTURA_TELA:
        tela.fill(PRETO)
        for sprite in janelas: sprite.rect.y += velocidade_scroll
        for sprite in plataformas: sprite.rect.y += velocidade_scroll
        for sprite in itens_bonus: sprite.rect.y += velocidade_scroll
        
        todos_sprites.draw(tela)
        
        texto = fonte_hud.render("PRÓXIMO NÍVEL!", True, BRANCO)
        rect_texto = texto.get_rect(center=(LARGURA_TELA//2, ALTURA_TELA//2))
        tela.blit(texto, rect_texto)
        
        pygame.display.flip()
        altura_scroll += velocidade_scroll
        pygame.time.delay(10)

# --- LOOP PRINCIPAL DA APLICAÇÃO ---
aplicacao_rodando = True

while aplicacao_rodando:
    # 0. TELA DE TÍTULO (NOVA)
    # Mostra a tela de título antes de carregar o menu de dificuldade
    mostrar_tela_titulo(tela)

    # 1. MENUS
    resultado_menu = mostrar_menu_dificuldade(tela)
    
    if resultado_menu is None:
        aplicacao_rodando = False
        break
        
    max_niveis, nome_dificuldade, modo_debug_ativo = resultado_menu
    modo_escolhido = mostrar_menu_modo(tela)

    # 2. PREPARAÇÃO DO JOGO
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

    # Cria Jogador
    jogador = Heroi(modo_escolhido, debug=modo_debug_ativo)
    todos_sprites.add(jogador)

    # Cria Vilão
    vilao = Inimigo()
    vilao.atualizar_dificuldade(nivel_atual, max_niveis, nome_dificuldade)
    todos_sprites.add(vilao)
    inimigos.add(vilao)

    # 3. LOOP DA PARTIDA (Gameplay)
    jogo_rodando = True
    while jogo_rodando:
        # --- LÓGICA DE TEMPO ---
        tempo_decorrido = (pygame.time.get_ticks() - tempo_inicio_nivel) / 1000
        tempo_restante = TEMPO_LIMITE_NIVEL - tempo_decorrido
        
        if tempo_restante <= 0:
            desenhar_tela_fim_de_jogo(tela, "TEMPO ESGOTADO!", VERMELHO, jogador.pontuacao, nome_dificuldade)
            jogo_rodando = False

        # --- EVENTOS ---
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                jogo_rodando = False; aplicacao_rodando = False
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    jogo_rodando = False # Volta ao menu

                # Ação de Consertar (Tecla C)
                if evento.key == pygame.K_c:
                    # Verifica se está no chão antes de consertar
                    pode_consertar = False
                    if jogador.modo == "CLASSICO":
                        if not jogador.pulando_classico:
                            pode_consertar = True
                    elif jogador.modo == "LIVRE":
                        if jogador.no_chao:
                            pode_consertar = True
                    
                    if pode_consertar:
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
                                        
                                        # Drop de Item a cada 5 consertos
                                        if jogador.contagem_consertos % 5 == 0:
                                            janelas_disponiveis = [j for j in janelas if j.quebrada]
                                            if janelas_disponiveis:
                                                j_alvo = random.choice(janelas_disponiveis)
                                                novo_item = ItemBonus(j_alvo.rect.centerx, j_alvo.rect.centery)
                                                todos_sprites.add(novo_item)
                                                itens_bonus.add(novo_item)
                            
                            if fez_algum_conserto:
                                jogador.iniciar_conserto()

                # Controles Específicos por Modo
                if jogador.modo == "LIVRE":
                    if evento.key == pygame.K_SPACE: jogador.pular_livre()
                elif jogador.modo == "CLASSICO":
                    if evento.key == pygame.K_LEFT:  jogador.mover_classico(-1, 0)
                    if evento.key == pygame.K_RIGHT: jogador.mover_classico(1, 0)
                    if evento.key == pygame.K_UP:    jogador.mover_classico(0, -1)
                    if evento.key == pygame.K_DOWN:  jogador.mover_classico(0, 1)

        # --- ATUALIZAÇÕES ---
        todos_sprites.update()
        
        # Colisão com plataformas no modo LIVRE
        if jogador.modo == "LIVRE" and not jogador.no_chao:
             colisoes = pygame.sprite.spritecollide(jogador, plataformas, False)
             for bloco in colisoes:
                if jogador.velocidade_y > 0 and jogador.rect.bottom < bloco.rect.bottom + 10:
                    jogador.rect.bottom = bloco.rect.top
                    jogador.velocidade_y = 0
                    jogador.no_chao = True
                    jogador.ultima_posicao_segura = (jogador.rect.centerx, jogador.rect.bottom)

        # Ataques do Vilão
        lista_de_tiros = vilao.tentar_atirar()
        for projetil in lista_de_tiros:
            todos_sprites.add(projetil)
            tijolos.add(projetil)
            perigos.add(projetil)

        # Spawna Urubus (Nível 3+)
        if nivel_atual >= 3:
            chance_urubu = 0.5 + (nivel_atual * 0.2)
            if random.random() * 100 < chance_urubu:
                novo_urubu = Urubu(nivel_atual)
                todos_sprites.add(novo_urubu)
                perigos.add(novo_urubu)

        # Coleta de Itens
        hits_itens = pygame.sprite.spritecollide(jogador, itens_bonus, True)
        for item in hits_itens:
            jogador.pontuacao += 300
            jogador.itens_coletados += 1
            if jogador.itens_coletados % 3 == 0:
                jogador.ativar_invencibilidade(6000, tipo="ITEM")

        # Colisão com Perigos (Tijolos/Urubus)
        hits = pygame.sprite.spritecollide(jogador, perigos, False)
        for ameaca in hits:
            if jogador.tomar_dano():
                ameaca.kill()

        # Verifica Derrota (Vidas)
        if jogador.vidas <= 0:
            desenhar_tela_fim_de_jogo(tela, "GAME OVER", VERMELHO, jogador.pontuacao, nome_dificuldade, ganhou=False)
            jogo_rodando = False

        # --- DESENHO ---
        # 1. Background Dinâmico
        if nivel_atual == 1:
            tela.blit(img_predio_inicio, (0, 0))
        elif nivel_atual == max_niveis:
            tela.blit(img_predio_topo, (0, 0))
        else:
            tela.blit(img_predio_meio, (0, 0))
            
        # 2. HUD (Fundo Escuro no Topo)
        bg_hud = pygame.Surface((LARGURA_TELA, 50))
        bg_hud.set_alpha(150)
        bg_hud.fill(PRETO)
        tela.blit(bg_hud, (0,0))
        
        # 3. HUD (Vidas)
        for i in range(jogador.vidas):
            tela.blit(img_vida, (10 + i * 45, 5))
        
        # 4. HUD (Texto)
        info_texto = f"Pts: {jogador.pontuacao} | Nível: {nivel_atual}/{max_niveis} | Tempo: {int(tempo_restante)}s"
        texto_hud = fonte_hud.render(info_texto, True, BRANCO)
        tela.blit(texto_hud, (160, 5))
        
        # 5. Sprites
        todos_sprites.draw(tela)
        pygame.display.flip()

        # --- VERIFICAÇÃO DE VITÓRIA DE NÍVEL ---
        janelas_quebradas = [j for j in janelas if j.quebrada]
        if len(janelas_quebradas) == 0:
            # Passou de fase!
            bonus_vidas = jogador.vidas * 500
            bonus_tempo = int(tempo_restante) * 10
            jogador.pontuacao += bonus_vidas + bonus_tempo
            
            if nivel_atual >= max_niveis:
                # Zerou o jogo
                desenhar_tela_fim_de_jogo(tela, "VOCÊ ZEROU O JOGO!", VERDE, jogador.pontuacao, nome_dificuldade, ganhou=True)
                jogo_rodando = False 
            else:
                # Próximo Nível
                for ameaca in perigos: ameaca.kill()
                for item in itens_bonus: item.kill()
                
                # Pequena cena de transição
                jogador.rect.y = 90
                jogador.rect.x = LARGURA_TELA // 2
                pygame.display.flip()
                pygame.time.wait(1000)
                
                transicao_fase()
                criar_cenario()
                
                # Reinsere personagens nos grupos
                todos_sprites.remove(jogador); todos_sprites.add(jogador)
                todos_sprites.remove(vilao); todos_sprites.add(vilao)
                
                # Reseta posições e status
                jogador.resetar_posicao()
                jogador.itens_coletados = 0 
                
                # Aumenta dificuldade
                nivel_atual += 1
                vilao.atualizar_dificuldade(nivel_atual, max_niveis, nome_dificuldade)
                tempo_inicio_nivel = pygame.time.get_ticks() 

        relogio.tick(FPS)

# Encerra
pygame.quit()
sys.exit()