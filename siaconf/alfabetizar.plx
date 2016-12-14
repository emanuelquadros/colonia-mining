#!/usr/bin/perl

##############################
# alfabetizar.plx
#
# Incrementa o alfabeto analisando o conjunto atual de caracteres conhecidos 
# contra os caracteres encontrados no corpus
#
##############################

use strict;

use lib '/home/manu/Dropbox/notes/yale/QuantitativeCorpus/romance-group-project/siaconf';
use Alfabeto;
use Data::Dumper;

binmode STDOUT, ":utf8";
binmode STDERR, ":utf8";



##############################
# Verificações de integridade
#
my $corpus = shift;
unless (defined $corpus) {
	print "Sintaxe: ./alfabetizar.plx <corpus>\n";
	exit 1;
}


unless (-e "$corpus") {
	print "Erro: corpus $corpus inexistente\n";
	exit 1;
}
unless (-d "$corpus") {
	print "Erro: arquivo $corpus existe, mas n\x{00e3}o \x{00e9} um diret\x{00f3}rio\n";
	exit 1;
}
unless (-e "$corpus/$corpus-sujo.txt") {
	print "Erro: arquivo $corpus/$corpus-sujo.txt n\x{00e3}o encontrado\n";
	exit 1;
}


unless (-e "$corpus/$corpus-sujo.txt") {
	print "Erro: arquivo $corpus/$corpus-sujo.txt n\x{00e3}o acess\x{00ed}vel\n";
	exit 1;
}
#
#############################


#############################
# Carrega o alfabeto
#
my $alfabeto = Alfabeto->new();
if (-e "./$corpus/alfa") {
	$alfabeto->carregar("./$corpus/alfa");
}
elsif (-e "./alfa") {
	$alfabeto->carregar("./alfa");
}
else {
	print "Erro: nenhum arquivo de alfabeto encontrado para o corpus $corpus\n";
	exit 1;
}
#
##############################



##############################
# Verifica o tamanho do arquivo para exibição interativa
#
print STDERR "Calculando tamanho do corpus corpus...";
my $tamanhocorpus = `wc './$corpus/$corpus-sujo.txt'`;
$tamanhocorpus =~ s/^[\s\t]*(\d+).*$/$1/;
print STDERR "\n";
#
##############################



##############################
# Processa o corpus
#
open CORPUS, "<:utf8", "./$corpus/$corpus-sujo.txt";

my %novos;
my $numlinha = 0;
my $existenovo = 0;
my $ultimoporcento = -1;
my $porcentagem;
while (!eof CORPUS) {
	my $linha = <CORPUS>;
	chomp $linha;
	$numlinha++;

	$porcentagem = int ($numlinha / $tamanhocorpus * 100);
	if ($porcentagem != $ultimoporcento) {
		print STDERR "\rBuscando simbolos... $porcentagem%";
		$ultimoporcento = $porcentagem;
	}
	
	my $impresso = 0;
	my @novos = $alfabeto->procurarnovos($linha);
	foreach my $novo (@novos) {
		unless (defined $novos{$novo}) {
			# Imprime a linha onde há ocorrências somente uma vez
			#
			unless ($impresso) {
				$| = 1;
				print "(Linha $numlinha) $linha\n";
				$impresso = 1;
			}

			$| = 1;
			printf "\t$novo (u%x)\n", ord $novo;
			$novos{$novo} = 1;
			$existenovo = 1;
		}
	}
	if ($impresso) {
		print "\n";
		$ultimoporcento = -1;  # Força o programa a imprimir porcentagem
	}
}
close CORPUS;
#
########################



unless ($existenovo) {
	print STDERR "\nNenhum s\x{00ed}mbolo novo encontrado";
}

print STDERR "\nFeito!  :)\n";
