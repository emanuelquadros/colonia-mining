package Alfabeto;

################################################################################
# Alfabeto.pm
#
# Auxilia na manipula��o da l�ngua atrav�s de um alfabeto personaliz�vel
#
# Autor: Rafael Giusti [rg.bacs@gmail.com]
#
################################################################################



use strict;


################################################################################
# M�todo:	new
# Prop�sito:	Constr�i um novo objeto da classe
# Entrada:	--
# Sa�da:	Um objeto da classe Alfabeto
# Detalhes:	--
#
################################################################################

sub new {
	my $proto = shift;
	my $class = ref $proto || $proto;

	my $self = bless {
		Conhecidos	=> {},  # Todos os que aparecen no arquivo de alfabeto
		Minimizar	=> {},  # Rela��o mai�scula --> min�scula
		Ordenar		=> {},  # Conjuntos de letras com valor de ordem
		Ignorar		=> {},  # S�mbolos desconsiderados na ordena��o
		Limpar		=> "",  # S�mbolos a serem removidos de uma string
		Quebrar		=> "",	# Delimitadores de palavras
	}, $proto;

	return $self;
}



################################################################################
# M�todo:	caracterizar
# Prop�sito:	Retorna um caractere, convertendo seq��ncias de escape
# Entrada:	Uma string que cont�m um caracter ou uma seq��ncia de escape
# Sa�da:	Um escalar que cont�m um �nico caracter
# Detalhes:	--
#
################################################################################

sub caracterizar {
	my $self = shift;
	my $car = shift;

	if ($car =~ /\\u{([0-9a-fA-F]+)}/) {
		return sprintf "%c", hex $1;
	}
	else {
		return $car;
	}
}



################################################################################
# M�todo:	proteger
# Prop�sito:	Assegura que um s�mbolo pode ser corretamente usado num conjunto
# 		[] de regexp
# Entrada:	Um s�mbolo
# Sa�da:	O s�mbolo ou uma seq��ncia de escape que represente o s�mbolo
# Detalhes:	--
#
################################################################################

my %trocas = (
	"["	=>	"\\[",
	"]"	=>	"\\]",
	"-"	=>	"\\-",
	"^"	=>	"\\^"
);

sub proteger {
	my $self    = shift;
	my $simbolo = shift;

	if (defined $trocas{$simbolo}) {
		return $trocas{$simbolo};
	}
	else {
		return $simbolo;
	}
}



################################################################################
# M�todo:	carregar
# Prop�sito:	Carrega informa��es de aflabeto a partir de um arquivo	
# Entrada:	Uma string que cont�m o caminho do arquivo a ser carregado
# Sa�da:	--	
# Detalhes:	--
#
################################################################################

sub carregar {
	my $self = shift;
	my $arquivo = shift;

	my $escopo = "nenhum";
	my $numlinha = 0;
	my $ordem = 0;

	my %escoposvalidos = (
		"MINIMIZAR" => 1, 
		"ORDEM" => 1,
		"IGNORAR" => 1,
		"LIMPAR" => 1,
		"QUEBRAR" => 1
	);
	
	# Limpa as configura��es para que o alfabeto possa ser trocado
	# dinamicamente
	#
	$self->{Minimizar} = {};
	$self->{Ordenar} = {};
	$self->{Ignorar} = {};
	$self->{Limpar} = "";
	$self->{Quebrar} = "";

	open ARQUIVO, "<:utf8", $arquivo or die "Cannot open $arquivo: $!";
	while (!eof ARQUIVO) {
		my $linha = <ARQUIVO>;
		$numlinha++;
		chomp $linha;
		$linha =~ s/#.*$//;
		$linha =~ s/^[\s\t]+//;
		next unless $linha =~ /[^\s\t]/;

		if ($linha =~ /::([A-Z]+)$/) {
			my $novoescopo = $1;
			if ($1 eq "FIM") {
				last;
			}
			elsif (defined $escoposvalidos{$novoescopo}) {
				$escopo = $novoescopo;
			}
			elsif ($novoescopo !~ /[^\t\s]/) {
				die "Escopo nulo na linha $numlinha do alfabeto $arquivo\n";
			}
			else { 
				die "Escopo desconhecido ($novoescopo) na linha $numlinha do alfabeto $arquivo\n";
			}
		}
		elsif ($escopo eq "MINIMIZAR") {
			$linha =~ /([^\s]+)\s+([^\s]+)/;
			$self->{Minimizar}->{$self->caracterizar($1)} = $self->caracterizar($2);
			$self->{Conhecidos}->{$self->caracterizar($1)} = 1;
			$self->{Conhecidos}->{$self->caracterizar($2)} = 1;
		}
		elsif ($escopo eq "ORDEM") {
			# O primeiro elemento do escopo ordenar tem ordem zero. Os elementos
			# seguintes t�m ordem incrementada. Quanto menor a ordem, maior
			# a preced�ncia do caracter
			#
			foreach my $letra (split /[\s\t]/, $linha) {
				$self->{Ordenar}->{$self->caracterizar($letra)} = $ordem;
				$self->{Conhecidos}->{$self->caracterizar($letra)} = 1;
			}
			$ordem++;
		}
		elsif ($escopo eq "IGNORAR") {
			$self->{Ignorar}->{$self->caracterizar($linha)} = 1;
			$self->{Conhecidos}->{$self->caracterizar($linha)} = 1;
		}
		elsif ($escopo eq "LIMPAR") {
			$self->{Limpar} = $self->{Limpar} . $self->proteger($self->caracterizar($linha));
			$self->{Conhecidos}->{$self->caracterizar($linha)} = 1;
		}
		elsif ($escopo eq "QUEBRAR") {
			$self->{Quebrar} = $self->{Quebrar} . $self->proteger($self->caracterizar($linha));
			$self->{Conhecidos}->{$self->caracterizar($linha)} = 1;
		}
		else {
			die "Escopo indefinido na linha $numlinha do alfabeto $arquivo\n";
		}
	}	
	close ARQUIVO;
}



################################################################################
# M�todo:	procurarnovos
# Prop�sito:	Procura s�mbolos desconhecidos numa string
# Entrada:	Uma string
# Sa�da:	Uma lista contendo todos os s�mbolos da string que n�o est�o
# 		registados no alfabeto	
# Detalhes:	--
#
################################################################################

sub procurarnovos {
	my $self = shift;
	my $linha = shift;

	$linha =~ s/[\s\t\r\n]//g;
	my @linha = split //, $linha;

	my @novos;
	foreach my $letra (@linha) {
		push @novos, $letra unless defined $self->{Conhecidos}->{$letra} ;
	}

	return @novos;
}



################################################################################
# M�todo:	_avancar [VISIBILIDADE PRIVADA (PRIVATE)]
# Prop�sito:	Utilizado durante a compara��o de duas strings: busca o pr�ximo
# 		caracter relevante para a tarefa de compara��o, ignorando 
# 		s�mbolos desconheciso ou listados no campo ::IGNORAR
# Entrada:	1. Uma refer�ncia para o �ndice do caracter
# 		2. Uma refer�ncia para a lista de caracteres
# Sa�da:	--
# Detalhes:	Verifique os detalhes do m�todo comparar
#
################################################################################

sub _avancar {
	my $self = shift;
	my $indice = shift;
	my $lista = shift;

	do {
		$$indice++;
	} while (($$indice < scalar @$lista) && ($self->{Ignorar}->{$lista->[$$indice]} || 
			!defined $self->{Ordenar}->{$lista->[$$indice]}));
}



################################################################################
# M�todo:	comparar
# Prop�sito:	Compara duas strings segundo as regras especificadas no arquivo
# 		do alfabeto
# Entrada:	1. Uma string A
# 		2. Uma string B
# Sa�da:	-1 se A � anterior a B na ordem lexicogr�fica
# 		 0 se A e B t�m mesma ordem (N�O implica A e B serem id�nticas)
# 		+1 se A � posterior a B na ordem lexicogr�fica
# Detalhes:	As duas strings s�o quebradas em caracteres, os quais s�o
# 		armazenados em listas. O m�todo _avancar � utilizado para iterar
# 		a lista. Somente caracteres relevantes para a compara��o s�o
# 		verificados
#
################################################################################

sub comparar {
	my $self = shift;
	my @a = split //, shift;
	my @b = split //, shift;
	my $i = -1;
	my $j = -1;

	# Avan�a os �ndices at� encontrar dois caracteres que possuem ordens 
	# diferentes ou at� que uma das listas seja inteiramente consumida
	#
	$self->_avancar(\$i, \@a);
	$self->_avancar(\$j, \@b);
	while (($i < scalar @a) && ($j < scalar @b) && 
			$self->{Ordenar}->{$a[$i]} == $self->{Ordenar}->{$b[$j]}) {
		$self->_avancar(\$i, \@a);
		$self->_avancar(\$j, \@b);
	}

	if ($i == scalar @a) {
		if ($j == scalar @b) {
			# Se ambas as listas foram inteiramente consumidas, as 
			# duas strings possuem mesma ordem
			#
			return 0;
		}
		else {
			# Se a string A foi inteiramente consumida, mas a string
			# B n�o, ent�o A � substring de B e vem antes na ordem
			# lexicogr�fica (ex: bola e bolacha)
			#
			return -1;
		}
	}
	else {
		if ($j == scalar @b) {
			# Se a string B foi inteiramente consumida, mas a string
			# A n�o, ent�o B � substring de A e vem antes na ordem
			# lexicogr�fica (ex: bolacha e bola)
			#
			return 1;
		}
		else {
			#return (ord $a[$i]) - (ord $b[$j]);
			return $self->{Ordenar}->{$a[$i]} - $self->{Ordenar}->{$b[$j]};
		}
	}
}



################################################################################
# M�todo:	minimizar
# Prop�sito:	Minimiza todos os caracteres de uma string utilizando as
# 		regras do alfabeto
# Entrada:	Uma string
# Sa�da:	A mesma string com todos os caracteres minimizados	
# Detalhes:	--
#
################################################################################

sub minimizar {
	my $self = shift;
	my @frase = split //, shift;
	
	my $saida = "";
	foreach my $letra (@frase) {
		if (defined $self->{Minimizar}->{$letra}) {
			$saida = $saida . $self->{Minimizar}->{$letra};
		}
		else {
			$saida = $saida . $letra;
		}
	}

	return $saida;
}



################################################################################
# M�todo:	limpar
# Prop�sito:	Remove da strings caracteres listados no campo ::LIMPAR	
# Entrada:	Uma string
# Sa�da:	Uma string, com v�rios s�mbolos removidos	
# Detalhes:	--
#
################################################################################

sub limpar {
	my $self = shift;
	my $str  = shift;
	my ($limpar);

	$limpar = "[$self->{Limpar}]";
	$str =~ s/$limpar//g;
	return $str;
}



################################################################################
# M�todo:	quebrar
# Prop�sito:	Quebra uma string em v�rias substrings em pontos definidos
# 		no campo ::QUEBRAR
# Entrada:	Uma string
# Sa�da:	Uma lista de palavras da string, sem brancos
# Detalhes:	--
#
################################################################################

sub quebrar {
	my $self = shift;
	my $str  = shift;
	my ($quebrar, @lista);

	$quebrar = "[$self->{Quebrar}]";
	@lista = split /$quebrar/, $str;
	return @lista;
}



return 1;
