# utils.py
import pygame
import os
import json
from config import *

def carregar_imagem(nome_arquivo, largura, altura, cor_fallback, pasta=""):
    caminho = os.path.join("assets", pasta, nome_arquivo)
    try:
        imagem = pygame.image.load(caminho).convert_alpha()
        imagem = pygame.transform.scale(imagem, (largura, altura))
        return imagem
    except Exception as e:
        print(f"AVISO: {nome_arquivo} não encontrado em '{caminho}'. Usando cor padrão.")
        img_fallback = pygame.Surface((largura, altura))
        img_fallback.fill(cor_fallback)
        return img_fallback

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