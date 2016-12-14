package Alfabeto;

################################################################################
# Alfabeto.pm
#
# Auxilia na manipulação da língua através de um alfabeto personalizável
#
# Autor: Rafael Giusti [rg.bacs@gmail.com]
#
################################################################################



use strict;


################################################################################
# Método:	new
# Propósito:	Constrói um novo objeto da classe
# Entrada:	--
# Saída:	Um objeto da classe Alfabeto
# Detalhes:	--
#
################################################################################

sub new {
	my $proto = shift;
	my $class = ref $proto || $proto;

	my $self = bless {
		Conhecidos	=> {},  # Todos os que aparecen no arquivo de alfabeto
		Minimizar	=> {},  # Relação maiúscula --> minúscula
		Ordenar		=> {},  # Conjuntos de letras com valor de ordem
		Ignorar		=> {},  # Símbolos desconsiderados na ordenação
		Limpar		=> "",  # Símbolos a serem removidos de uma string
		Quebrar		=> "",	# Delimitadores de palavras
	}, $proto;

	return $self;
}



################################################################################
# Método:	caracterizar
# Propósito:	Retorna um caractere, convertendo seqüências de escape
# Entrada:	Uma string que contém um caracter ou uma seqüência de escape
# Saída:	Um escalar que contém um único caracter
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
# Método:	proteger
# Propósito:	Assegura que um símbolo pode ser corretamente usado num conjunto
# 		[] de regexp
# Entrada:	Um símbolo
# Saída:	O símbolo ou uma seqüência de escape que represente o símbolo
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
# Método:	carregar
# Propósito:	Carrega informações de aflabeto a partir de um arquivo	
# Entrada:	Uma string que contém o caminho do arquivo a ser carregado
# Saída:	--	
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
	
	# Limpa as configurações para que o alfabeto possa ser trocado
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
			# seguintes têm ordem incrementada. Quanto menor a ordem, maior
			# a precedência do caracter
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
# Método:	procurarnovos
# Propósito:	Procura símbolos desconhecidos numa string
# Entrada:	Uma string
# Saída:	Uma lista contendo todos os símbolos da string que não estão
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
# Método:	_avancar [VISIBILIDADE PRIVADA (PRIVATE)]
# Propósito:	Utilizado durante a comparação de duas strings: busca o próximo
# 		caracter relevante para a tarefa de comparação, ignorando 
# 		símbolos desconheciso ou listados no campo ::IGNORAR
# Entrada:	1. Uma referência para o índice do caracter
# 		2. Uma referência para a lista de caracteres
# Saída:	--
# Detalhes:	Verifique os detalhes do método comparar
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
# Método:	comparar
# Propósito:	Compara duas strings segundo as regras especificadas no arquivo
# 		do alfabeto
# Entrada:	1. Uma string A
# 		2. Uma string B
# Saída:	-1 se A é anterior a B na ordem lexicográfica
# 		 0 se A e B têm mesma ordem (NÃO implica A e B serem idênticas)
# 		+1 se A é posterior a B na ordem lexicográfica
# Detalhes:	As duas strings são quebradas em caracteres, os quais são
# 		armazenados em listas. O método _avancar é utilizado para iterar
# 		a lista. Somente caracteres relevantes para a comparação são
# 		verificados
#
################################################################################

sub comparar {
	my $self = shift;
	my @a = split //, shift;
	my @b = split //, shift;
	my $i = -1;
	my $j = -1;

	# Avança os índices até encontrar dois caracteres que possuem ordens 
	# diferentes ou até que uma das listas seja inteiramente consumida
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
			# B não, então A é substring de B e vem antes na ordem
			# lexicográfica (ex: bola e bolacha)
			#
			return -1;
		}
	}
	else {
		if ($j == scalar @b) {
			# Se a string B foi inteiramente consumida, mas a string
			# A não, então B é substring de A e vem antes na ordem
			# lexicográfica (ex: bolacha e bola)
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
# Método:	minimizar
# Propósito:	Minimiza todos os caracteres de uma string utilizando as
# 		regras do alfabeto
# Entrada:	Uma string
# Saída:	A mesma string com todos os caracteres minimizados	
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
# Método:	limpar
# Propósito:	Remove da strings caracteres listados no campo ::LIMPAR	
# Entrada:	Uma string
# Saída:	Uma string, com vários símbolos removidos	
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
# Método:	quebrar
# Propósito:	Quebra uma string em várias substrings em pontos definidos
# 		no campo ::QUEBRAR
# Entrada:	Uma string
# Saída:	Uma lista de palavras da string, sem brancos
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
