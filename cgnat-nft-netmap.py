#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''# -*- coding: latin-1 -*-'''

'''
GRCN is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
#
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
#
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

import os
import sys
import time
import ipaddress

__author__ = 'Beiriz & Gondim'
__version__= 1.000
__datebegin__= "27/07/2020 (28/05/2023)"
__com1__ = "add rule ip nat"

#-----------------------------------------------------------------------
fazer_regras_in = False #Este valor deve ser alterado para True caso haja interesse de gerar também as regras de CGNAT no sentido IN: 'fazer_regras_in = True'. OBS: CGNAT do tipo OUT sempre serão geradas.
indice = 0
txt_publico = ""
txt_privado = ""
qt_ips_publicos = 0 #Quantidade de IPs públicos na rede informada
qt_ips_privados = 0 #Quantidade de IPs privados na rede informada
qt_ips_privados_por_ip_publico = 0 #Quantos IPs privados vão sair por um único IP público ( A relação PRI/PUB)
qt_portas_por_ip = 2016 #quantidade de portas que serão reservadas por IP privado.
numero_porta_incial = 1024
numero_porta_final = 65535
relacao = '1/32'
qt_total_portas = (numero_porta_final-(numero_porta_incial-1))
#As 2 confs abaixo trabalham em conjunto para ajustar o range total de portas de cada IP público
relacao_portas = {'1/4':16128, '1/8':8064, '1/16':4032, '1/32':2016, '1/64':1008, '1/128':504, '1/256':252}
relacao_mascara = {'1/4':30, '1/8':29, '1/16':28, '1/32':27, '1/64':26, '1/128':25, '1/256':24}
relacao_ips_masq = {'1/4':4, '1/8':8, '1/16':16, '1/32':32, '1/64':64, '1/128':128, '1/256':256}
#-------------------------------------------------

os.system('cls' if os.name == 'nt' else 'clear')
titulo = "GRCN - Gerador de Regras CGNAT em nftables (NETMAP) - %s - v%s - %s" % (__author__, __version__,__datebegin__)
print("#"*106)
print("    %s" %(titulo))
print("#"*106)

#------------------------------------------------- Parâmetros informados / manual:

try:
  #Indice:
  indice = int(sys.argv[1])
  #Blocos:
  txt_publico = str(sys.argv[2])
  txt_privado = str(sys.argv[3])
  #RELAÇÃO_IP_PUBLICO_X_CLIENTE
  try:
    relacao = str(sys.argv[4])
  except:
    relacao = '1/32'
  finally:
    qt_portas_por_ip = relacao_portas[relacao]
    print("\n\t[ Ídice inicial: %i | público: %s | privado: %s | %i portas/IP (%s)]\t\n" % (indice, txt_publico, txt_privado, qt_portas_por_ip, relacao))

except:
  print("\nErro! Informe pelo menos os parâmetros obrigatórios deste script.\n")
  print("## Manual de Instruções:")
  print("\n###### Exemplo básico (1/32):\n")
  print("```")
  print("%spython %s <INDICE> <BLOCO_PUBLICO> <BLOCO_PRIVADO>" %(' '*6, sys.argv[0]))
  print("%spython %s 0 192.0.2.0/24 100.69.0.0/22" %(' '*6, sys.argv[0]))
  print("```")
  print("\n###### Exemplo avançado:\n")
  print("```")
  print("%s python %s <INDICE> <BLOCO_PUBLICO> <BLOCO_PRIVADO> <RELAÇÃO_IP_PUBLICO_X_CLIENTE>(OPCIONAL)" %(' '*6, sys.argv[0]))
  print("%s python %s 0 192.0.2.0/24 100.69.0.0/22 1/16")
  print("```")
  print("\n###### Parâmetros:\n")
  print("* INDICE: Inteiro >=0 que vai ser o sufixo do nome das regras únicas. Exemplo *CGNATOUT_XXX*;\n")
  print("* BLOCO_PUBLICO: É o bloco de IPs públicos por onde o bloco CGNAT vai sair para a internet. Exemplo: *192.0.2.0/24*\n")
  print("* BLOCO_PRIVADO: É o bloco de IPs privados que serão entregues ao assinante.\n")
  print("* RELAÇÃO_IP_PUBLICO_X_CLIENTE (OPCIONAL):")
  print("    - 1/4   - 16128 portas por IP;")
  print("    - 1/8   - 8064 portas por IP;")
  print("    - 1/16  - 4032 portas por IP;")
  print("    - 1/32  - 2016 portas por IP (Configuração padrão, quando este último parâmetro não é informado);")
  print("    - 1/64  - 1008 portas por IP (Atenção! Não recomendado pelas boas práticas);")
  print("    - 1/128 - 504 portas por IP (Atenção! Não recomendado pelas boas práticas);")
  print("    - 1/256 - 252 portas por IP (Atenção! Não recomendado pelas boas práticas);")
  print("\n####### Observações:\n")
  print("* Este script vai dividir o <BLOCO_PRIVADO> em N sub-redes privadas. Cada sub-rede privada sai por um único IP público e dela, cada IP privado sai com uma fração das portas de seu IP público.\n")
  print("* Se <BLOCO_PUBLICO> for um /24 e <BLOCO_PRIVADO> um /19 e a relação for 1/32, serão colocados exatamente 32 IPs privados (assinantes) atrás de um IP público. Cada IP privado vai sair com 2016 portas de seu IP público (65535-1023)/32. O famoso *1:32*.\n")
  print("\n")
  print("\nATENÇÃO! Por boas práticas, o script PAROU de gerar as regras CGNAT do tipo IN. Caso queira continuar gerando-as, edite o cgnat-nft.py, alterando o valor *fazer_regras_in* de *False* para *True*;")
  print("\nFIM deste manual!\n")
  exit(0)
#------------------------------------------------- trata os parâmetros informados:

try:
  if sys.version_info >= (3,0):
    rede_publica = ipaddress.ip_network(str(txt_publico), strict=False)
    rede_privada = ipaddress.ip_network(str(txt_privado), strict=False)
  else:
    rede_publica = ipaddress.ip_network(unicode(txt_publico), strict=False)
    rede_privada = ipaddress.ip_network(unicode(txt_privado), strict=False)
  qt_ips_publicos = int(rede_publica.num_addresses)
  qt_ips_privados = int(rede_privada.num_addresses)
  qt_ips_privados_por_ip_publico = int( qt_ips_privados / qt_ips_publicos )
  # Nome arquivo de destino
  nome_arquivo_regras = ("cgnat-%i-%i.conf" % (indice,(indice + qt_ips_publicos - 1)))
  nome_arquivo_tabela = ("tabela-%i-%i.txt" % (indice,(indice + qt_ips_publicos - 1)))
  # calcula a máscara das subnets privadas baseado na relação PRI/PUB:
  subnets_privadas = list(rede_privada.subnets(new_prefix=relacao_mascara[relacao]))
  subnets_publicas = list(rede_publica.subnets(new_prefix=relacao_mascara[relacao]))
except:
  print("\nErro! Informe parâmetros válidos para este script:\n\nRespeite a relação de IP público x IP privado: 1:32, 1:16, 1:8, etc\n\nEncerrando!\n")
  exit(0)

if (qt_ips_publicos * relacao_ips_masq[relacao]) > qt_ips_privados:
   print("\nErro! Quantidade de IPs privados insuficiente!")
   exit(0)

print(" - Índice das regras: %i;" % (indice))
print(" - Rede pública: %s (%i IPs);" % (txt_publico,qt_ips_publicos))
print(" - Rede privada: %s (%i IPs);" % (txt_privado,qt_ips_privados))
print(" - Quantidade de IPs privados por IP público: %i (%i sub-redes /%i);" % (qt_ips_privados_por_ip_publico, qt_ips_publicos, relacao_mascara[relacao]))
print(" - Total de portas públicas: %i;" % (qt_total_portas))
print(" - Portas por IP privado: %i;" % (qt_portas_por_ip))
print(" - Arquivo de destino (conf): '%s';" % (nome_arquivo_regras))
print(" - Arquivo de tabela (txt): '%s';" % (nome_arquivo_tabela))
print("\n")

if fazer_regras_in:
  print("\nATENÇÃO!\n  Variável fazer_regras_in=True\n  Mesmo não sendo boas práticas, SERÃO geradas regras de CGNAT do tipo IN!\n")

#------------------------------------------------- Abre o arquivo onde as regras serão armazenadas (destino) e tabela de relacionamento de portas (tabela):
try:
  caminho_deste_script = os.path.dirname(os.path.realpath(__file__))+'/'
  arquivo_regras = open(caminho_deste_script+nome_arquivo_regras, "w")
except (OSError, IOError) as e:
  print ("\nErro!\nFalha ao abrir a escrita do arquivo onde as regras serão armazenadas (destino)")
  sys.exit(1)

try:
  caminho_deste_script = os.path.dirname(os.path.realpath(__file__))+'/'
  arquivo_tabela = open(caminho_deste_script+nome_arquivo_tabela, "w")
except (OSError, IOError) as e:
  print ("\nErro!\nFalha ao abrir a escrita do arquivo onde as regras serão armazenadas (tabela)")
  sys.exit(1)

arquivo_regras.write("# %s\n" %(titulo))
arquivo_regras.write("# - blocos %s -> %s;\n# - %i de IPs privados / IP público;\n# - %i portas / IP privado;\n" %(
  txt_privado,
  txt_publico,
  qt_ips_privados_por_ip_publico,
  qt_portas_por_ip
))

arquivo_tabela.write("# %s\n" %(titulo))
arquivo_tabela.write("# - blocos %s -> %s;\n# - %i de IPs privados / IP público;\n# - %i portas / IP privado;\n" %(
  txt_privado,
  txt_publico,
  qt_ips_privados_por_ip_publico,
  qt_portas_por_ip
))

#-------------------------------------------------------------------------- principal

if sys.version_info >= (3,0):
  input("Tecle [ENTER]...")
else:
  raw_input("Tecle [ENTER]...")
momento_incial = time.time()

print("\n")
indice_subnet_privada = 0
indice_subnet_publica = 0
# Zera o range de portas para o prox IP publico
porta_ini = numero_porta_incial
# guarda valor de indice inicial
porta_fim = (numero_porta_incial + (qt_portas_por_ip -1))
for ip_publico in rede_publica:
  arquivo_regras.write("# %s #INDICE %i / PREFIXO PUBLICO %s\n" % ('-' * 40, indice, str(ipaddress.ip_network(subnets_publicas[indice_subnet_publica]))))
  print("VALOR: %s" % (str(ipaddress.ip_network(subnets_publicas[indice_subnet_publica]))))
  arquivo_regras.write("add chain ip nat CGNATOUT_%i\n" % (indice))
  if fazer_regras_in:
    arquivo_regras.write("add chain ip nat CGNATIN_%i\n" % (indice))
  arquivo_regras.write("flush chain ip nat CGNATOUT_%i\n" % (indice))
  if fazer_regras_in:
    arquivo_regras.write("flush chain ip nat CGNATIN_%i\n" % (indice))
  subnetpriv = subnets_privadas[indice_subnet_privada]
  subnetpub = subnets_publicas[indice_subnet_publica]
  print("%s INDICE=%i - PREFIXO_PUBLICO=%s -> SUBNET_PRIVADA_%i=%s" % ("=" * 40, indice, str(ipaddress.ip_network(subnets_publicas[indice_subnet_publica])), (indice_subnet_privada+1), str(subnetpriv)))
  ip_privado = ipaddress.ip_network(subnetpriv)
  ip_publico = ipaddress.ip_network(subnetpub)
  trp = "%i-%i" % (porta_ini,porta_fim)
  print("%s IP PRIVADO %s:%s" %("-"*60,str(ip_privado),trp))
  #Regras para montagem do netmap
  arquivo_regras.write("%s CGNATOUT_%i meta l4proto { tcp, udp } counter snat ip prefix to ip saddr map { %s : %s . %s }\n" % (
    __com1__,
    indice,
    str(ip_privado),
    str(ip_publico),
    trp
  ))

  if fazer_regras_in:
    arquivo_regras.write("%s CGNATIN_%i meta l4proto { tcp, udp } counter dnat ip prefix to ip daddr map { %s : %s . %s }\n" % (
      __com1__,
      indice,
      str(ip_publico),
      str(ip_privado),
      trp
    ))

  arquivo_regras.write("%s CGNATOUT_%i counter snat ip prefix to ip saddr map { %s : %s }\n" % (
    __com1__,
    indice,
    str(ip_privado),
    str(ip_publico)
  ))
  arquivo_regras.write("%s CGNATOUT ip saddr %s counter jump CGNATOUT_%i\n" % (
    __com1__,
    str(subnetpriv),
    indice
  ))
  if fazer_regras_in:
    arquivo_regras.write("%s CGNATIN ip daddr %s counter jump CGNATIN_%i\n" % (
      __com1__,
      str(ip_publico),
      indice
    ))

  # Gera tabela de corelacao de IPs e portas para quebra de sigilo tecnologico
  for ip_publico, ip_privado in zip(ipaddress.ip_network(subnetpub),ipaddress.ip_network(subnetpriv)):
      arquivo_tabela.write("%s \t %s \t %s\n" % (str(ip_privado),str(ip_publico),trp))

  indice+=1
  indice_subnet_privada+=1
  print("porta: %i porta: %i" % (porta_ini,porta_fim))
  #incrementa o range de portas para o próximo IP privado
  porta_ini += qt_portas_por_ip
  porta_fim += qt_portas_por_ip
  if porta_fim > numero_porta_final:
     # muda subnet publica e inicializa portas
     indice_subnet_publica+=1
     porta_ini = numero_porta_incial
     porta_fim = (numero_porta_incial + (qt_portas_por_ip -1))

#-------------------------------------------------------------------------- final

#Fecha o arquivo onde as regras serão armazenadas e a tabela de relacionamento:
try:
  arquivo_regras.close()
except (OSError, IOError) as e:
  print ("\nErro!\nFalha ao salvar o arquivo onde as regras serão armazenadas (destino)")
  sys.exit(1)

try:
  arquivo_tabela.close()
except (OSError, IOError) as e:
  print ("\nErro!\nFalha ao salvar o arquivo onde as regras serão armazenadas (tabela)")
  sys.exit(1)

print("\nFIM!\n\nAs regras foram geradas no arquivo:\n%s\n\nTabela salva no arquivo:\n%s\n\nDuração: %.3f segundos" % (
  caminho_deste_script + nome_arquivo_regras,
  caminho_deste_script + nome_arquivo_tabela,
  (time.time()-momento_incial)
))
