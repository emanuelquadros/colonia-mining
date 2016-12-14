#!/usr/bin/perl

# importar.plx
#
# Importa um único arquivo (ou um conjunto de arquivos) como corpus.
#


use strict;

use File::Temp qw(tempdir);
use Data::Dumper;

binmode STDIN, ":utf8";
binmode STDOUT, ":utf8";


########################################################################################################
#
# FUNÇÕES
#

sub reckognize {
	my $file = shift;
	my ($encoding);

	$encoding = `file '$file'`;

	if ($encoding =~ /ascii text$/i) {
		return "iso8859-9";
	}
	elsif ($encoding =~ /mpeg adts/i) {
		return "utf16";
	}
	elsif ($encoding =~ /utf-(\d+)/i) {
		return "utf$1";
	}
	elsif ($encoding =~ /iso-8859[^-]/i) {
		return "iso8859-9";
	}
	elsif ($encoding =~ /iso-(\d+)-(\d+)/i) {
		return "iso$1-$2";
	}
	elsif ($encoding =~ /iso-(\d+)/i) {
		return "iso$1";
	}
	elsif ($encoding =~ /[^:]*:\s*(.+)\s+text$/i) {
		return "$1";
	}
	else {
		return undef;
	}
}



sub encode_utf8 {
	my $input = shift;
	my $output = shift;
	my ($encoding, $result);

	$encoding = reckognize($input);
	unless (defined $encoding) {
		unless ($encoding =~ /[^\t\s\n\r]/) {
			$encoding = "<null>";
		}
		die "encode_utf8(\$input, \$output) - cannot reckognize input" .
				" file\'s encoding\n\t$input resembles the " .
				"follwoing encoding: $encoding\n";
	}

	$result = `iconv -f $encoding -t utf8 '$input' -o '$output'`;
	if (defined $result and $result =~ /[^\t\s\n\r]/) {
		die "encode_utf8(\$input, \$output) - error converting from " .
				"$encoding to utf-8.\n" .
				"\tSystem returned: $result\n";
	}
}



sub cat {
	my $output = shift;
	my @input = @_;
	my ($current);

	open OUTPUT, ">:utf8", $output or
			die "cat(\$output, \@input) - cannot open $output " .
			"for writing: $!";
	
	for $current (@input) {
		unless (open INPUT, "<:utf8", $current) {
			close OUTPUT;
			die "cat(\$output, \@input) - cannot open $current " .
					"for reading: $!";
		}
		
		while (<INPUT>) {
			print OUTPUT $_;
		}
		close INPUT;
	}

	close OUTPUT;
}


#
#
#######################################################################################################


my $nome = shift @ARGV;

unless (defined $nome and scalar @ARGV) {
	print "Sintaxe: ./importar.plx <nome> <arquivos>\n";
	exit;
}

my $diretorio = "./$nome";
if (-e $diretorio) {
	unless (-d $diretorio) {
		print "Erro: $diretorio existe e n\x{00e3}o \x{00e9} um diret\x{00f3}rio.\n";
		exit;
	}
	unless (-x $diretorio and -r $diretorio and -w $diretorio) {
		print "Erro: n\x{00e3}o possuo os privil\x{00e9}gios necess\x{00e1}rios para " .
				"utilizar o diret\x{00f3}rio $diretorio.\n";
		exit;
	}
}
else {
	unless (-w "./") {
		print "Erro: n\x{00e3}o possuo os privil\x{00e9}gio necess\x{00e1}rios para " .
				"criar o diret\x{00f3}rio $diretorio.\n";
		exit;
	}
	unless (mkdir $diretorio) {
		print "Erro: n\x{00e3}o consegui criar o diret\x{00e1}rio $diretorio.\n";
		print "O sistema retornou a seguinte mensagem: $!\n";
		exit;
	}
	
}


print "Importando corpus $nome\n";
print "Buscando arquivos parciais...";
my @candidatos = @ARGV;
my @arquivos;
my %erros;
foreach my $possivel (@candidatos) {
	unless (-e $possivel) {
		$erros{$possivel} = "Objeto n\x{00e3}o encontrado.";
		next;
	}
	unless (-r $possivel) {
		$erros{$possivel} = "N\x{00e3}o \x{00e9} poss\x{00ed}vel ler o objeto.";
		next;
	}
	if (-d $possivel) {
		unless (-x $possivel) {
			$erros{$possivel} = "Diret\x{00f3}rio n\x{00e3}o execut\z{00e1}vel.";
			next;
		}
		my @novos = <$possivel/*>;
		push @candidatos, @novos;
	}
	elsif (-f $possivel) {
		push @arquivos, $possivel;
	}
	else {
		$erros{$possivel} = "Objeto desconhecido";
		next;
	}
}
my $numarquivos = scalar @arquivos;
if ($numarquivos) {
	my $s = $numarquivos > 1 ? "s " : " ";
	print " $numarquivos arquivo${s}encontrado$s\n";
}
else {
	print " nenhum arquivo encontrado\n";
	exit;
}

if (keys %erros) {
	print "Erros detectados!\n";
	foreach my $arquivo (keys %erros) {
		print "$arquivo: $erros{$arquivo}\n";
	}
	exit;
}

my $erros = 0;
my $tempdir = tempdir(CLEANUP => 1);
my @temparq;
my $arq = 0;
print "Convertendo para UTF-8\n";
foreach my $arquivo (@arquivos) {
	my $codificao = reckognize($arquivo);
	if (!defined $codificao) {
		print "$arquivo: codifica\x{00e7}\x{00e3}o desconhecida ($codificao)\n";
		$erros++;
	}
	elsif ($codificao eq "utf8") {
		print "$arquivo: j\x{00e1} \x{00e9} UTF-8\n";
		push @temparq, "$arquivo";
		$arq++;
	}	
	else {
		print "$arquivo: convertendo de $codificao\n";
		encode_utf8($arquivo, "$tempdir/$arq");
		push @temparq, "$tempdir/$arq";
		$arq++;
	}
}
if ($erros) {
	my $s = $erros > 1 ? "s " : " ";
	print "$erros erro${s}encontrado$s\n";
	exit;
}

if (scalar @temparq > 1) {
	print "Mesclando arquivos... ";
	cat("$nome/$nome-sujo.txt", @temparq);
}
else {
	`cp '$temparq[0]' '$nome/$nome-sujo.txt'`;
}
print "Feito!   :)\n";
