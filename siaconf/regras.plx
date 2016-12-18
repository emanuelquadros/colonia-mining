#!/usr/bin/perl

use strict;
use lib './';
use Alfabeto;
use FileHandle;
use Data::Dumper;

binmode STDIN, ":utf8";
binmode STDOUT, ":utf8";

my $nome = shift;
unless (defined $nome) {
	print "Sintaxe: ./regras.plx <nome>\n";
	exit;
}

my $corpus = "$nome/$nome.txt";
my $perdidas = "$nome/corr-$nome-perdidas.txt";
my $corrigidas = "$nome/corr-$nome-corrigidas.txt";
my $clusters = "$nome/corr-$nome-clusters.txt";
my $regras = "$nome/corr-$nome-regras.txt";

my $alfabeto = Alfabeto->new();
$alfabeto->carregar("$nome/alfa") // $alfabeto->carregar("alfa") // die "Cannot open alphabet";


###################
# Carrega o léxico
#
my %lexico;
$| = 1;
print "Carregando lexico...";
open(LEXICO, "<:utf8", "$nome/lexico") || open(LEXICO, "<:utf8", "lexico") || die "Cannot find a lexicon";
my $conta = 0;
while (!eof LEXICO) {
	my $palavra = <LEXICO>;
	chomp $palavra;
	$lexico{$palavra} = 1;
	$conta++;
}
close LEXICO;
print " $conta palavras carregadas\n";


###################
# Carrega as regras
#
sub proximo {
	my $textoref = shift;

	$$textoref =~ s/^[\s\t]+//;
	if ($$textoref =~ /\"([^"]+)\"(.*)/ or $$textoref =~ /([^ ]+)(.*)/) {
		$$textoref = $2;
		return $1;
	}
	else {
		return undef;
	}
}

my @handle;

my @regras;
my $linha = 0;
$| = 1;
print "Carregando regras...";
open(REGRAS, "<:utf8", "$nome/regras") || open(REGRAS, "<:utf8", "regras") || die "Can't find the rules!";
my $cont = 0;
while (!eof REGRAS) {
	my $texto = <REGRAS>;
	chomp $texto;
	my $original = $texto;
	
	my $contexto = proximo(\$texto);
	my $velho = proximo(\$texto);
	my $novo = proximo(\$texto);

	$linha++;
	unless ((defined $contexto) and (defined $velho) and (defined $novo)) {
		print "Erro na linha $linha: $original\n";
	}
	else {
		$handle[$cont] = new FileHandle ">$regras.$cont";
		binmode $handle[$cont], ":utf8";
		$cont++;
		push @regras, [$contexto, $velho, $novo];
	}
}
close REGRAS;
print((scalar @regras) . " regras carregadas\n");


##################
# Aplica as regras
#
my ($linha, $regracobre, $palavracoberta, %clusters, @regrasquecobrem);

print "Aplicando regras\n";

open CORPUS, "<:utf8", $corpus;
open PERDIDAS, ">:utf8", $perdidas;
open CORRIGIDAS, ">:utf8", $corrigidas;

my $maiorlargura = 0;
my $largura;

my %perdidas;
my %contagem;

#open AUSDABA, ">:utf8", "$nome-ausdaba";

$linha = 0;
while (!eof CORPUS) {
	my $velha = <CORPUS>;
	chomp $velha;
	$velha = $alfabeto->minimizar($velha);
	my $nova = $velha;
	$contagem{$velha}++;

#print AUSDABA "\n\nPalavra $velha\n";

	unless ($velha =~ /[^\t\s]/) {
		next;
	};

	if ($lexico{$velha}) {
		$perdidas{$velha} = 1;
	#print AUSDABA "Esta no lexico, entao eu to vazando\n";
		next; 
	}
	
	@regrasquecobrem = ();
	$palavracoberta = 0;
	foreach my $regraindice (0 .. scalar @regras - 1) {
		my $regra = $regras[$regraindice];
		$regracobre = 0;
		my $SHITDETECTOR = 0;
		my $skip = 0;
	#print AUSDABA "Testando a regra $regra->[0] $regra->[1] $regra->[2]\n";
		while (!$skip) {
		#print AUSDABA "Iterando\n";
			if ($nova =~ /($regra->[0])/) {
				if ($SHITDETECTOR++ == 100) {
					print "Porquera!!!! Loop infinito!\n";
					print "Palavra original: $velha\n";
					print "Regra: $regra->[0] $regra->[1] $regra->[2]\n";
					print "Contexto: $1\n";
					print "Modificada: $nova\n";
					print "Saindo...\n\n";
					exit;
				}
				my $contexto = $1;
				if ($contexto =~ s/$regra->[1]/$regra->[2]/) {
					$nova =~ s/$regra->[0]/$contexto/;
					$regracobre = $palavracoberta = 1;
				#print AUSDABA "\tCobre!\n";
				}
				else {
					$skip = 1;
				#print AUSDABA "\tCai no contexo, mas nao substituia\n";
				}
			}
			else {
			#print AUSDABA "\tNao cobre\n";
				$skip = 1;
			}
		}

		if ($regracobre) {
			#push @regrasquecobrem, "($regra->[0] $regra->[1] $regra->[2])";
			#push @{$clusters{$nova}->{$velha}}, "($regra->[0] $regra->[1] $regra->[2])";
			#print AUSDABA "Adicionando regra ao vetor da palavra\n";
			#unless (defined @{$clusters{$nova}->{$velha}}) {
			#	@{$clusters{$nova}->{$velha}} = ();
			#}
			#print AUSDABA "Vetor tem scalar " . (scalar @{$clusters{$nova}->{$velha}}) . "\n";
			#push @{$clusters{$nova}->{$velha}}, $regraindice;
			#print AUSDABA "Inserido.\n";
			#print AUSDABA "Vetor tem scalar " . (scalar @{$clusters{$nova}->{$velha}}) . "\n";
			#$handle[$regraindice]->print("$velha -> $nova\n");

			push @regrasquecobrem, $regraindice;

			$largura = length($nova) + length($velha);
			if ($largura > $maiorlargura) {
				$maiorlargura = $largura;
			}
		}
	}

	#$clusters{$nova}->{$velha} = 1;
	
	if ($palavracoberta) {
		#print CORRIGIDAS ($lexico{$velha} ? "=>" : "->") . "$velha " . 
		#		 ($lexico{$nova} ? "=>" : "->") . " $nova\t";
		#foreach my $regra (@regrasquecobrem) {
		#	print CORRIGIDAS "$regra  ";
		#}
		#print CORRIGIDAS "\n";
		foreach my $regraindice (@regrasquecobrem) {
			push @{$clusters{$nova}->{$velha}}, $regraindice;
		}
	}
	else {
		#print PERDIDAS "$velha\n";
		#unless ($lexico{$velha}) {
		$perdidas{$velha} = 1;
		#}
	}

	$linha++;
	#$| = 1;
	print "\rPalavra $linha";
}

close CORPUS;
#close CORRIGIDAS;
#close PERDIDAS;

print "\rOk! :)         \n";

print "Gerando relat\x{00f3}rios...\n";

#undef %lexico;
open CLUSTERS, ">:utf8", $clusters;
my @novas = keys %clusters;


#print "PERDIDAS\n";
#print Dumper %perdidas;

#print "\n\nCLUSTERS\n";
#print Dumper %clusters;


#print "\n\nNOVAS PALAVRAS\n\n";
#print Dumper @novas;

my %tamanho = ();
foreach my $nova (@novas) {
	my $tamanho = 0;
	my @velhas = keys %{$clusters{$nova}};
	my $novafoi = 0;
	foreach my $velha (@velhas) {
		$tamanho += $contagem{$velha};
		if ($velha eq $nova) {
			$novafoi = 1;
		}
	}
	if (!$novafoi && $perdidas{$nova}) {
		$tamanho += $contagem{$nova};
	}
	$tamanho{$nova} = $tamanho;
}

@novas = sort { ($tamanho{$b} <=> $tamanho{$a}) or $alfabeto->comparar($a, $b) } @novas;
foreach my $nova (@novas) {

	my @velhas = keys %{$clusters{$nova}};

	#print "\n\nPALAVRA NOVA: $nova\n";
	#print "VELHAS:\n\n";
	#print Dumper @velhas;
	
	#if (!%${$clusters{$nova}}{$nova} && $perdidas{$nova}) {
	#	$velhas{$nova} = 1;
	#}

	#@velhas = keys %{$clusters{$nova}};
	#print "\n\nINSERCAO DA NOVA NO CLUSTER\n\n";
	#print Dumper @velhas;
	
	my @velhas2 = @velhas;
	if (!defined $clusters{$nova}->{$nova} && $perdidas{$nova}) {
		push @velhas2, $nova;
		$perdidas{$nova} = "out";
	}
	
	@velhas2 = sort { ($contagem{$b} <=> $contagem{$a}) or $alfabeto->comparar($a, $b) } @velhas2;
	#if ((!(defined $clusters{$nova}->{$nova}) && $perdidas{$nova}) || scalar @velhas > 1) {
	if (scalar @velhas2 > 1) {
		print CLUSTERS "$nova  ($tamanho{$nova})\n";
		#my $novafoi = 0;
		foreach my $velha (@velhas2) {
			#if ($velha eq $nova) {
			#	$novafoi = 1;
			#}
			print CLUSTERS "\t$velha\t\t($contagem{$velha})\n";
		}
		#if (!$novafoi && $perdidas{$nova}) {
		#	print CLUSTERS "\t$nova\t\t($contagem{$nova})\n";
		#}
		print CLUSTERS "\n";
	}
	foreach my $velha (@velhas)  {
		print CORRIGIDAS ($lexico{$velha} ? "=>" : "->") . " $velha " . 
		                 ($lexico{$nova} ? "=>" : "->") . " $nova    ";
		$largura = length($velha) + length($nova);
		while ($largura < $maiorlargura) {
			print CORRIGIDAS " ";
			$largura++;	
		}
		
		my @indices = @{$clusters{$nova}->{$velha}};
		##int CORRIGIDAS "[" . (scalar @indices) . "] ";
		@indices = sort { $a <=> $b } @indices;
		my $ultimo = -1;
		#foreach my $regra (@{$clusters{$nova}->{$velha}}) {
		foreach my $indice (@indices) {
			#print CORRIGIDAS "$indice ";
			if ($indice == $ultimo) {
				next;
			}
			$ultimo = $indice;
			print CORRIGIDAS "($regras[$indice]->[0] $regras[$indice]->[1] $regras[$indice]->[2]) ";
			$handle[$indice]->print("$velha -> $nova\n");
		}
		print CORRIGIDAS "\n";
	}
}
close CLUSTERS;
close CORRIGIDAS;

my @perdidas = keys %perdidas;
undef %perdidas;
@perdidas = sort { ($contagem{$b} <=> $contagem{$a}) or $alfabeto->comparar($a, $b) } @perdidas;
foreach my $perdida (@perdidas) {
	unless ($lexico{$perdida} || $perdidas{$perdida} eq "out") {
		print PERDIDAS "$perdida\t\t($contagem{$perdida})\n";
	}
}
close PERDIDAS;
undef %lexico;
undef %perdidas;

foreach my $handle (@handle) {
	$handle->close();
}
open REGRAS, ">:utf8", $regras;
for my $i (0 .. scalar @regras - 1) {
	open UMA, "<:utf8", "$regras.$i";
	print REGRAS "$regras[$i]->[0] $regras[$i]->[1] $regras[$i]->[2]\n";
	while (!eof UMA) {
		my $linha = <UMA>;
		print REGRAS "\t$linha";
	}
	close UMA;
	print REGRAS "\n";
}
close REGRAS;

for my $i (0 .. scalar @regras - 1) {
	unlink "$regras.$i";
}
