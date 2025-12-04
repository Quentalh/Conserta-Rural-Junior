# ui.py
import pygame
import sys
from config import *
from utils import carregar_imagem, atualizar_highscore

def get_fonte():
    # Cria a fonte aqui para garantir que o pygame já iniciou
    return pygame.font.SysFont("Arial", 40, bold=True)

# --- NOVA FUNÇÃO: TELA DE TÍTULO ---
def mostrar_tela_titulo(tela):
    pygame.event.clear() # Limpa cliques antigos
    
    # Carrega a imagem da tela de título
    img_titulo = carregar_imagem("tela_titulo.png", LARGURA_TELA, ALTURA_TELA, PRETO, pasta="telas")
    
    esperando = True
    while esperando:
        # Desenha a imagem
        tela.blit(img_titulo, (0, 0))
        pygame.display.flip()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if evento.type == pygame.KEYDOWN:
                # Se apertar ENTER (Return) ou Enter do Numpad
                if evento.key == pygame.K_RETURN or evento.key == pygame.K_KP_ENTER:
                    esperando = False

def mostrar_menu_dificuldade(tela):
    pygame.event.clear()
    fonte = get_fonte()
    bg_menu = carregar_imagem("menu_dificuldade.png", LARGURA_TELA, ALTURA_TELA, PRETO, pasta="menu")
    menu_ativo = True
    input_codigo = ""
    debug_ativado = False
    
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
            "1 - Fácil (4 Níveis)", "2 - Médio (6 Níveis)", 
            "3 - Difícil (8 Níveis)", "4 - Dificílimo (10 Níveis + Ataque Especial)",
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

def mostrar_menu_modo(tela):
    pygame.event.clear()
    fonte = get_fonte()
    bg_menu = carregar_imagem("menu_dificuldade.png", LARGURA_TELA, ALTURA_TELA, PRETO, pasta="menu")
    menu_ativo = True
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

def desenhar_tela_fim_de_jogo(tela, mensagem, cor, pontuacao_final, dificuldade_nome, ganhou=False):
    fonte = get_fonte()
    img_tela_vitoria = carregar_imagem("tela_vitoria.png", LARGURA_TELA, ALTURA_TELA, VERDE, pasta="telas")
    img_tela_gameover = carregar_imagem("tela_gameover.png", LARGURA_TELA, ALTURA_TELA, VERMELHO, pasta="telas")
    
    if ganhou: tela.blit(img_tela_vitoria, (0, 0))
    else: tela.blit(img_tela_gameover, (0, 0))
    
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
                if evento.key == pygame.K_SPACE: esperando = False