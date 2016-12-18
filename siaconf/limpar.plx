#!/usr/bin/perl

use strict;

use lib './';
use Alfabeto;



################################
# Verificações de integridade
#
my $corpus = shift;
unless (defined $corpus) {
	print "Sintaxe: ./limpar.plx <corpus>\n";
	exit 1;
}


unless (-e "./$corpus") {
	print "Erro: corpus $corpus inexistente\n";
	exit 1;
}
unless (-d "./$corpus") {
	print "Erro: corpus $corpus existe, mas n\x{00e3}o \x{0009} um diret\x{00f3}rio\n";
	exit 1;
}
unless (-e "./$corpus/$corpus-sujo.txt") {
	print "Erro: arquivo $corpus/$corpus-sujo.txt n\x{00e3}o existe\n";
	exit 1;
}
unless (-r "./$corpus/$corpus-sujo.txt") {
	print "Erro: arquivo $corpus/$corpus-sujo.txt n\x{00e3}o acess\x{00ed}vel\n";
	exit 1;
}
#
################################



###############################
# Carrega o alfabeto
#
my $alfa = new Alfabeto;
if (-e "./$corpus/alfa") {
	$alfa->carregar("./corpus/alfa");
}
elsif (-e "./alfa") {
	$alfa->carregar("./alfa");
}
else {
	die "Arquivo de alfabeto n\x{00e3}o encontrado\n";
}
#
################################



################################
# Descobre a quantidade de linhas do arquivo com wc
#
$| = 1;
print "Calculando tamanho do corpus...";
my $totallinhas = `wc $corpus/$corpus-sujo.txt`;
$totallinhas =~ s/^(\s*\d+).*$/$1/;
print "\n";
#
###############################



################################
# Efetua a "limpeza"
#
open SUJO, "<:utf8", "$corpus/$corpus-sujo.txt";
open LIMPO, ">:utf8", "$corpus/$corpus.txt";
my $linhanum = 0;
my $ultimaporcentagem =-1;
my ($porcentagem, $numpalavras);
while (!eof SUJO) {
	my $linha = <SUJO>;
	chomp $linha;

	# Calcula e imprime a porcentagem do processo
	#
	$porcentagem = int (++$linhanum / $totallinhas * 100);
	if ($porcentagem != $ultimaporcentagem) {
		$| = 1;
		print "\rLimpando corpus... $porcentagem%";
		$ultimaporcentagem = $porcentagem;
	}

	$linha =~ s/{[^{]*}//g;
	$linha =~ s/[0-9]+\^?\.?[aoAO]//g;
	foreach my $palavra ($alfa->quebrar($linha)) {
		if ($palavra =~ /[^\s\t]/) {
			$numpalavras++;
			print LIMPO $alfa->limpar($palavra) . "\n";
		}
	}
}
close LIMPO;
close SUJO;
#
################################



################################
# Transforma a quantidade de palavras num numero bonito com casas decimais
# e imprime a mensagem final
#
my $numerobonito = $numpalavras % 1000;
$numpalavras = int ($numpalavras / 1000);
while ($numpalavras) {
	$numerobonito = ($numpalavras % 1000) . ".$numerobonito";
	$numpalavras = int ($numpalavras / 1000);
}

print "\rLimpando corpus... $numerobonito palavras encontradas\n";
print "Feito!   :)\n";
#
##################################
