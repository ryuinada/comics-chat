#!/usr/local/bin/perl

# バッファリングしない
#
$| = 1;

# Jcode.pmを使う
#
# $kanji:　　ブラウザへ表示させる漢字コード(UTF8)
# $p_kanji:　UNIXプロセスが使う漢字コード(EUC)
#
use Jcode;
$kanji = 'utf8';
$p_kanji = 'utf8';


# chat file location
#
#$CHAT_HOME = "/export/home/users/akiyama/public_html/collaborate";
$CHAT_HOME = "/home/akiyama/public_html/collaborate";
$HREF_HOME = "collaborate";
$MEMBER_DIR = "$CHAT_HOME/member";
$MEMBER_FILE = "$MEMBER_DIR/members";
$FACE_FILE = "$CHAT_HOME/faces";
$TEMP_FILE = "$CHAT_HOME/chat.$$";
$LAST_MSG_FILE = "$CHAT_HOME/chat.last.msg";
$DUP_CHECK_FILE = "$CHAT_HOME/dupcheck";
$BODY_FILE = "$CHAT_HOME/chat.body";
$LOG_FILE = "$CHAT_HOME/chat.log";
$LOCK_FILE = "$CHAT_HOME/chat.lock";
$COUNT_FILE = "$CHAT_HOME/chat.count";
$QUOTE_TIMES = 6;

# for flock
#
$LOCK_SH = 1;
$LOCK_EX = 2;
$LOCK_NB = 4;
$LOCK_UN = 8;

sub lock {
  flock (LOCK, $LOCK_EX);
  seek (LOCK, 0, 2);
}

sub unlock {
  flock (LOCK, $LOCK_UN);
}

# OUTへ$fileを書き出すサブルーチン
#
sub file_print {
  local(*OUT, $file) = @_;
  local $/;
  open (IN, $file);
  $the_file = <IN>;
  print OUT $the_file;
  close (IN);
}

sub file_print2 {
  local(*OUT, $file) = @_;
  local $/;
  open (IN, $file);
  $the_file = <IN>;
  $the_file =~ s/\<IMG/\<III/gmoi;
  $the_file =~ s/\<HR\>/\<BR\>/gmoi;
  $the_file =~ s/\<B\>/\<BB\>/gmoi;
  $the_file =~ s/\<STRONG\>//gmoi;
  print OUT $the_file;
  close (IN);
}

# メンバーリストの読み込み
#
open (MEMBERS, "$MEMBER_FILE");
while (<MEMBERS>) {
  chomp;
  s/\*/.\*/g;
  ($host, $name) = split(/,/);
  $myname{$host} = $name;
}
close (MEMBERS);

# 顔文字リストの読み込み
#
open (FACES, "$FACE_FILE");
while (<FACES>) {
  chomp;
  ($name, $face) = split(/,/);
  $face{$name} = $face;
}
close (FACES);

# 日付の設定
# 
$now = time();
($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now);
$thisday = ("日", "月", "火", "水", "木", "金", "土")[$wday];
$year = $year + 1900;
$mmon = $mon + 1;
$date = "$year.$mmon.$mday($thisday)　";
Jcode::convert(\$date, $kanji, $p_kanji);

# データの読み込みと解析
#
if ($ENV{'REQUEST_METHOD'} eq 'POST') {
    read(STDIN, $input, $ENV{'CONTENT_LENGTH'});
}
elsif ($ENV{'REQUEST_METHOD'} eq 'GET') {
    $input = $ENV{'QUERY_STRING'};
}
@pairs = split(/&/, $input);

foreach (@pairs) {
    ($name, $value) = split(/=/, $_);
    $name  =~ tr/+/ /;
    $value =~ tr/+/ /;
    $name =~ s/%([\dA-Fa-f][\dA-Fa-f])/pack("C", hex($1))/eg;
    $value =~ s/%([\dA-Fa-f][\dA-Fa-f])/pack("C", hex($1))/eg;
    Jcode::convert(\$name, $p_kanji, $kanji);
    Jcode::convert(\$value, $p_kanji, $kanji);
    $field{$name} = $value;
}

# 匿名処理
#
$shimei = $field{'myname'};
if ($shimei =~ /匿名/) {
    $ENV{'REMOTE_HOST'} = 'secret';
}

# 名前が入っていないときは、ホスト名にしたがって
# 名前を検索してセットする。見つからない場合は
# ホスト名をセットする
#
$host = $ENV{'REMOTE_HOST'};
$addr = $ENV{'REMOTE_ADDR'};

if ($gethostbyaddr) {
	if ($host eq "" || $host eq "$addr") {
		$host = gethostbyaddr(pack("C4", split(/\./, $addr)), 2);
	}
}
if ($host eq "") { $host = $addr; }

$identify = quotemeta '*';
if ($field{'myname'} =~ /^$identify/) {
    $star = 1;
    $field{'myname'} =~ s/$identify//g;
}
unless (length($field{'myname'})) {
    $val = '';
    foreach $key (keys %myname) {
        if ($host =~ /$key/) {
            $val = $myname{$key};
        }
    }
    if ($val eq '') {
        $val = $host;
    }
    $field{'myname'} = $val;
    $name_null = 1;
}


# 再表示
#
if ($field{'option'} eq "再表示") {
    $kakikake = $field{'comment'};
    $field{'comment'}="";
}


# 重複ポストのチェック
# 　メッセージについてくる固有IDでチェックする
#
open (DUP_CHECK, "$DUP_CHECK_FILE");
while (<DUP_CHECK>) {
  if (/$field{'dupcheck'}/o) {
      $field{'comment'}="";
  }
}
close (DUP_CHECK);

# アクセス経過時間でオンラインメンバーをチェックする
# 　デフォルトは1時間
#
if ($field{'since'} eq "") {
    $field{'since'} = '1';
}

MEMBER: while (glob ("$MEMBER_DIR/*")) {
  next if /$MEMBER_DIR\/member/;
  $filename = $_;
  $diff = -C $filename;
  $val = '';
  if ($diff * 24 < $field{'since'}) {
      foreach $key (keys %myname) {
	if (/$key/) {
            $val = $myname{$key};
	}
      }
      if ($val eq '') {
	next MEMBER unless (-s $filename);
        $val = "<FONT COLOR=red>未登録</FONT>";
      }
      if (($online{$val} == 0) || ($online{$val} > $diff)) {
          $online{$val} = $diff;
      }
  }
}

foreach $key (keys %online) {
  $min_diff = $online{$key} * 24 * 60;
  $date_diff = sprintf "%d",$min_diff / 60 / 24;
  if ($date_diff >= 1) {
    $val = sprintf "%3dd %3d:%02d", $date_diff, $min_diff / 60 - $date_diff * 24 , $min_diff % 60;
  }
  elsif ($min_diff > 60) {
    $val = sprintf "%9d:%02d", $min_diff / 60, $min_diff % 60;
  }
  else {
    $val = sprintf "%12d",$min_diff;
  }
  $interval = "$val<BR>\n";
  push (@online, $interval.$key);
}
@sort_uniq = sort grep ((! $founded{$_}++), @online);
$sort_uniq = @sort_uniq;



# リロードのみのためにtouch
#
utime ($now, $now, "$MEMBER_DIR/$host") || open (TMP, ">> $MEMBER_DIR/$host");

# メッセージ欄が空白文字のみのコメントは無視する
#
if (!($field{'comment'} =~ /\S/)) {
    $field{'comment'}="";
}

## リロードや、メッセージ欄が空で「書き込み」した場合は処理されない
## 書き込みがある場合のメインルーチン
##
if (length($field{'comment'})) {

    # メッセージの処理
    #
    $com_tmp = $field{'comment'};

    # 改行文字を統一する
    #
    $com_tmp =~ s/\x0D\x0A/\n/g;
    $com_tmp =~ tr/\x0D\x0A/\n\n/;

    # HTMLタグの正規表現 $tag_regex

    $tag_regex_ = q{[^"'<>]*(?:"[^"]*"[^"'<>]*|'[^']*'[^"'<>]*)*(?:>|(?=<)|$(?!\n))}; #'}}}}
    $comment_tag_regex =
	'<!(?:--[^-]*-(?:[^-]+-)*?-(?:[^>-]*(?:-[^>-]+)*?)??)*(?:>|$(?!\n)|--.*$)';
    $tag_regex = qq{$comment_tag_regex|<$tag_regex_};

    # http URL の正規表現 $http_URL_regex

    $digit = q{[0-9]};
    $alpha = q{[a-zA-Z]};
    $alphanum = q{[a-zA-Z0-9]};
    $hex = q{[0-9A-Fa-f]};
    $escaped = qq{%$hex$hex};
    $uric = q{(?:[-_.!~*'()a-zA-Z0-9;/?:@&=+$,]} . qq{|$escaped)};
    $fragment = qq{$uric*};
    $query = qq{$uric*};
    $pchar = q{(?:[-_.!~*'()a-zA-Z0-9:@&=+$,]} . qq{|$escaped)};
    $param = qq{$pchar*};
    $segment = qq{$pchar*(?:;$param)*};
    $path_segments = qq{$segment(?:/$segment)*};
    $abs_path = qq{/$path_segments};
    $port = qq{$digit*};
    $IPv4address = qq{$digit+\\.$digit+\\.$digit+\\.$digit+};
    $toplabel = qq{$alpha(?:} . q{[-a-zA-Z0-9]*} . qq{$alphanum)?};
    $domainlabel = qq{$alphanum(?:} . q{[-a-zA-Z0-9]*} . qq{$alphanum)?};
    $hostname = qq{(?:$domainlabel\\.)*$toplabel\\.?};
    $host = qq{(?:$hostname|$IPv4address)};
    $hostport = qq{$host(?::$port)?};
    $userinfo = q{(?:[-_.!~*'()a-zA-Z0-9;:&=+$,]|} . qq{$escaped)*};
    $server = qq{(?:$userinfo\@)?$hostport};
    $authority = qq{$server};
    $scheme = q{(?:https?|shttp)};
    $net_path = qq{//$authority(?:$abs_path)?};
    $hier_part = qq{$net_path(?:\\?$query)?};
    $absoluteURI = qq{$scheme:$hier_part};
    $URI_reference = qq{$absoluteURI(?:#$fragment)?};
    $http_URL_regex = q{\b} . $URI_reference;
    $ftp_URL_regex = q{\b} . $URI_reference;
            
    # メールアドレスの正規表現 $mail_regex

    $esc         = '\\\\';               $Period      = '\.';
    $space       = '\040';
    $OpenBR      = '\[';                 $CloseBR     = '\]';
    $NonASCII    = '\x80-\xff';          $ctrl        = '\000-\037';
    $CRlist      = '\n\015';
    $qtext       = qq/[^$esc$NonASCII$CRlist\"]/;
    $dtext       = qq/[^$esc$NonASCII$CRlist$OpenBR$CloseBR]/;
    $quoted_pair = qq<${esc}[^$NonASCII]>;
    $atom_char   = qq/[^($space)<>\@,;:\".$esc$OpenBR$CloseBR$ctrl$NonASCII]/;
    $atom        = qq<$atom_char+(?!$atom_char)>;
    $quoted_str  = qq<\"$qtext*(?:$quoted_pair$qtext*)*\">;
    $word        = qq<(?:$atom|$quoted_str)>;
    $domain_ref  = $atom;
    $domain_lit  = qq<$OpenBR(?:$dtext|$quoted_pair)*$CloseBR>;
    $sub_domain  = qq<(?:$domain_ref|$domain_lit)>;
    $domain      = qq<$sub_domain(?:$Period$sub_domain)*>;
    $local_part  = qq<$word(?:$Period$word)*>;
    $addr_spec   = qq<$local_part\@$domain>;
    $mail_regex  = $addr_spec;

# $str の中の URI(URL) にリンクを張った $result を作る
# $tag_regex と $tag_regex_ は別途参照
# $http_URL_regex と $ftp_URL_regex および $mail_regex は別途参照

$str = $com_tmp;

    $text_regex = q{[^<]*};

    $result = '';  $skip = 0;
    while ($str =~ /($text_regex)($tag_regex)?/gso) {
	last if $1 eq '' and $2 eq '';
	$text_tmp = $1;
	$tag_tmp = $2;
	if ($skip) {
	    $result .= $text_tmp . $tag_tmp;
	    $skip = 0 if $tag_tmp =~ /^<\/[aA](?![0-9A-Za-z])/;
	} else {
	    $text_tmp =~ s{($http_URL_regex|$ftp_URL_regex|($mail_regex))}
	    {my($org, $mail) = ($1, $2);
	     (my $tmp = $org) =~ s/"/&quot;/g;
                   '<A HREF="' . ($mail ne '' ? 'mailto:' : '') . "$tmp\">$org</A>"}ego;
            $result .= $text_tmp . $tag_tmp;
            $skip = 1 if $tag_tmp =~ /^<[aA](?![0-9A-Za-z])/;
            if ($tag_tmp =~ /^<(XMP|PLAINTEXT|SCRIPT)(?![0-9A-Za-z])/i) {
              $str =~ /(.*?(?:<\/$1(?![0-9A-Za-z])$tag_regex_|$))/gsi;
              $result .= $1;
            }
          }
        }

$com_tmp = $result;

open (IN, $LOG_FILE);
@all = <IN>;
close (IN);

$i = 0;

foreach $all (@all) {
    if ($all[$i] =~ /<A NAME="(\d+.\d+)"/) {
	$num = $1;
	$tmp_name = $all[$i];
	$tmp_name =~ /<STRONG>(.+)<\/STRONG>/;
	chomp($tmp_name);

	$tmp_msg = $1.$all[$i+1];
	Jcode::convert(\$tmp_msg, $p_kanji, $kanji);
	$dmsg[$num] = $tmp_msg;

        $tmp_msg =~ s/<([^>]*)>//gmoi;
        $tmp_msg =~ s/\"//g;
        $tmp_msg =~ s/>//g;
        $tmp_msg =~ s/<//g;
	chomp($tmp_msg);

	$msg[$num] = $tmp_msg;
    }
$i++;
}

    # Number:へのジャンプ
    #
    $com_tmp =~ s/> *> *(\d+)/<A HREF="#$1.$wday" TITLE="$msg[$1]">>>$1<\/A>/gmoi;
    $com_tmp =~ s/(\d+) *> *>/<A HREF="#$1.$wday" TITLE="$msg[$1]">$1>><\/A>/gmoi;
    $com_tmp =~ s/＞ *(\d+)/<A HREF="#$1.$wday" TITLE="$msg[$1]">＞$1<\/A>/gmoi;
    $com_tmp =~ s/(\d+) *＞/<A HREF="#$1.$wday" TITLE="$msg[$1]">$1＞<\/A>/gmoi;
    $com_tmp =~ s/》 *(\d+)/<A HREF="#$1.$wday" TITLE="$msg[$1]">》$1<\/A>/gmoi;
    $com_tmp =~ s/(\d+) *》/<A HREF="#$1.$wday" TITLE="$msg[$1]">$1》<\/A>/gmoi;

    # 引用部分の色を変える
    # JPerlではないので、[>＞》]とまとめると誤マッチする
    #
    $com_tmp =~ s/^> *> *> *(.+)(\n|$)/<FONT COLOR="#ff6347">>>> $1<\/FONT>$2/gmoi;
    $com_tmp =~ s/^> *> *(.+)(\n|$)/<FONT COLOR="#0000cd">>> $1<\/FONT>$2/gmoi;
    $com_tmp =~ s/^> *(.+)(\n|$)/<FONT COLOR="#773377">> $1<\/FONT>$2/gmoi;

    $com_tmp =~ s/^＞ *＞ *＞ *(.+)(\n|$)/<FONT COLOR="#ff6347">>>> $1<\/FONT>$2/gmoi;
    $com_tmp =~ s/^＞ *＞ *(.+)(\n|$)/<FONT COLOR="#0000cd">>> $1<\/FONT>$2/gmoi;
    $com_tmp =~ s/^＞ *(.+)(\n|$)/<FONT COLOR="#773377">> $1<\/FONT>$2/gmoi;

    $com_tmp =~ s/^》 *》 *》 *(.+)(\n|$)/<FONT COLOR="#ff6347">>>> $1<\/FONT>$2/gmoi;
    $com_tmp =~ s/^》 *》 *(.+)(\n|$)/<FONT COLOR="#0000cd">>> $1<\/FONT>$2/gmoi;
    $com_tmp =~ s/^》 *(.+)(\n|$)/<FONT COLOR="#773377">> $1<\/FONT>$2/gmoi;

    # ハートマークの書き換え
    #
    $com_tmp =~ s/heart_mr/<FONT FACE=Symbol COLOR=red>ｩ<\/FONT>/gmoi;
    $com_tmp =~ s/heart_mg/<FONT FACE=Symbol COLOR=green>ｩ<\/FONT>/gmoi;
    $com_tmp =~ s/heart_mb/<FONT FACE=Symbol COLOR=blue>ｩ<\/FONT>/gmoi;
    $com_tmp =~ s/heart_mp/<FONT FACE=Symbol COLOR=pink>ｩ<\/FONT>/gmoi;
    $com_tmp =~ s/heart_m/<FONT FACE=Symbol COLOR=red>ｩ<\/FONT>/gmoi;


    # $com_tmp の先頭の空白文字(全角スペース含)を削除する
    $Zspace = '(?:\xA1\xA1)';
    $com_tmp =~ s/^(?:\s|$Zspace)+//o;

    # $com_tmp の末尾の空白文字(全角スペース含)を削除する
    $eucpre = qr{(?<!\x8F)};
    $com_tmp =~ s/$eucpre(?:\s|$Zspace)+$//o;


    # 改行文字を<BR>へ変換する
    #
    $com_tmp =~ s/\x0D\x0A/<BR>/g;
    $com_tmp =~ s/\x0D/<BR>/g;
    $com_tmp =~ s/\x0A/<BR>/g;

    $com_tmp =~ s/(<BR>)+$//g;

    # メッセージの処理が終わったのでShift_JISへ変換し,元に戻す
    #
    Jcode::convert(\$com_tmp, $kanji, $p_kanji);
    $field{'comment'} = $com_tmp;



    # 名前の処理
    #
    $com_tmp = $field{'myname'};

    # ハートマークの書き換え
    #
    $com_tmp =~ s/heart_mr/<FONT FACE=Symbol COLOR=red>ｩ<\/FONT>/gmoi;
    $com_tmp =~ s/heart_mg/<FONT FACE=Symbol COLOR=green>ｩ<\/FONT>/gmoi;
    $com_tmp =~ s/heart_mb/<FONT FACE=Symbol COLOR=blue>ｩ<\/FONT>/gmoi;
    $com_tmp =~ s/heart_mp/<FONT FACE=Symbol COLOR=pink>ｩ<\/FONT>/gmoi;
    $com_tmp =~ s/heart_m/<FONT FACE=Symbol COLOR=red>ｩ<\/FONT>/gmoi;

    # 本人判定
    # 　名前欄に「*」のみを入力した場合の処理
    #
    $identify = quotemeta '*';
    $com_tmp =~ s/$identify//g;
    $identify = quotemeta '&';
    $com_tmp =~ s/$identify//g;

    if ($star && $name_null) {
        $com_tmp = '*'.$com_tmp;
    }

    # 名前の処理が終わったのでShift_JISへ変換し,元に戻す
    #
    Jcode::convert(\$com_tmp, $kanji, $p_kanji);
    $field{'myname'} = $com_tmp;


    # 顔文字をShift_JISに変換
    #
    $face = $face{$field{'feeling'}};
    Jcode::convert(\$face, $kanji, $p_kanji);

    # ファイルロック開始
    #
    open (LOCK, ">> $LOCK_FILE");
    &lock();

    # 二重書き込みを防止するためメッセージIDを書き込む
    #
    open (DUP_CHECK, ">> $DUP_CHECK_FILE");
    print DUP_CHECK $field{'dupcheck'},"\n";
    close (DUP_CHECK);

    # メッセージのカウンタを１つ上げる
    #
    open(COUNT, "< $COUNT_FILE");
    $count = <COUNT>;
    close(COUNT);

    $count++;
 
    open(COUNT, "> $COUNT_FILE");
    print(COUNT "$count");
    close(COUNT);
 
    # 今回書き込まれたメッセージをテンポラリファイルに作成
    #
    open (FORM, "> $TEMP_FILE");

    print FORM "<TABLE><TR><TD>\n";
    print FORM "<A NAME=\"$count.$wday\"> </A><STRONG>$count: $field{'myname'} $face </STRONG>:";
    print FORM $date;
    printf FORM "%2.2d:%2.2d:%2.2d<BR>\n", $hour, $min, $sec ;
    print FORM $field{'comment'},"\n" ;
    print FORM "</TD></TR></TABLE>\n";
    print FORM "<HR>\n" ;

    close (FORM);

    # 今回書き込まれたメッセージをファイルへ保存
    # 　過去のファイルを回転させた後,メッセージを作って保存する
    #
    $loop = $QUOTE_TIMES;
    while ($loop) {
	$q_old = $loop - 1;
	$q_new = $loop - 2;
	open (OUT, "> $LAST_MSG_FILE.$q_old");
	file_print (*OUT, "$LAST_MSG_FILE.$q_new");
	close (OUT);
	$loop--;
    }

    $san = "さん：";
    Jcode::convert(\$san, $kanji, $p_kanji);
    $last_msg = ">>$count  "
	.$field{'myname'}."$san<BR>\n".$field{'comment'}."<BR>\n" ;

    open (OUT, ">$LAST_MSG_FILE.0");
    print OUT $last_msg;
    close (OUT);


    # ログファイルに追加書き出し
    #
    open (FORM, ">> $LOG_FILE");
    file_print (*FORM, "$TEMP_FILE");
    close (FORM);

    # 曜日別のファイルにコピー
    open (WDAY, "> $LOG_FILE.$wday.html");
    file_print (*WDAY, "$LOG_FILE");
    close (WDAY);

    # テンポラリファイルにこれまで書き込まれたメッセージ(chat.body)を追加
    #
    open (FORM, ">> $TEMP_FILE");
    file_print (*FORM, "$BODY_FILE");
    close (FORM);

    # 本日のログを作成（順序を逆転させる）
    #
    open (LOG, "$LOG_FILE");
    open (LOGR, "> $LOG_FILE.r");

    while(<LOG>){
      print LOGR $_;
      last if m!</HEAD>!;
    }
    $/="<HR>\n";
    print LOGR (reverse(<LOG>));
    $/="\n";

    close (LOG);
    close (LOGR);

    # 新しいchat.bodyの作成
    #
    rename ($TEMP_FILE, $BODY_FILE);

    # ファイルロック終了
    #
    &unlock();
    close (LOCK);

Jcode::convert(\$field{'myname'}, $p_kanji, $kanji);
}


# TITLEの取得
#
open (LOG, "$LOG_FILE.r");

$flag = 0;
while(<LOG>){
  next if /^\s*$/;
  next if /^<BR>\s*$/;
  chomp;
  if ($flag == 1) {
      chomp;
      $title = $_;
      last;
  }
  if (/<\/STRONG>/o) {
      $flag =1;
  }
}

close (LOG);

# TITLEからHTMLのタグを削除
#
Jcode::convert(\$title, $p_kanji, $kanji);
$title =~ s/＞/>/moi;
$title =~ s/<([^>]*)>//gmoi;
Jcode::convert(\$title, $kanji, $p_kanji);

# ＨＴＭＬをブラウザに戻す
#
if ($kanji eq "jis") {
    print "Content-type: text/html; charset=ISO-2022-JP\n";
}
if ($kanji eq "sjis") {
    print "Content-type: text/html; charset=Shift_JIS\n";
}

#print "Pragma: no-cache\n\n";
print "\n";
print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">',"\n";
print '<META HTTP-EQUIV="Pragma" CONTENT="no-cache">',"\n";
print '<META HTTP-EQUIV="Cache-Control" CONTENT="no-cache">',"\n";
print '<META HTTP-EQUIV="Expires" CONTENT="0">',"\n";
print '<HTML lang="ja">',"\n";
print "<HEAD>\n\n";


# リフレッシュを指示されている場合にはMETAタグを書き込む
#
if ($field{'refresh'} eq "") {
    $field{'refresh'} = 'never';
}
if ($field{'refresh'} ne 'never') {
    print '<META HTTP-EQUIV="Refresh" CONTENT="',$field{'refresh'},
    ';URL=',$ENV{'SCRIPT_NAME'},
    '?refresh=',$field{'refresh'},
    '&since=',$field{'since'},
    '&quiet=',$field{'quiet'},
    '">',"\n";
}
if ($kanji eq "jis") {
    print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; CHARSET=ISO-2022-JP">',"\n";
}
if ($kanji eq "sjis") {
    print '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; CHARSET=Shift_JIS">',"\n";
}


# TITLEを書く
#
print "<TITLE>$title</TITLE>\n\n";
print "<STYLE type=text/css>\n\n";
print "<!--\n\n";
print "A:visited {text-decoration:none;}\n\n";
print "A:link {text-decoration:underline;}\n\n";
print "A:hover {color=red;text-decoration:underline;}\n\n";
print "A:active {color=olive;text-decoration:underline;}\n\n";
# print "BODY{font-family:'MS UI Gothic';}\n\n";
# print "TD{font-family:'MS UI Gothic';}\n\n";
print "-->\n\n";
print "</STYLE>\n\n";

print '<SCRIPT language="JavaScript">',"\n";
print '<!--',"\n";

print 'function removetags(str) {',"\n";
print '    var poslt, posgt, result;',"\n";
print '    poslt = str.indexOf("<");',"\n";
print '    posgt = str.indexOf(">");',"\n";
print '    if(poslt < posgt) result = str.substring(0, poslt);',"\n";
print '    else {',"\n";
print '        result = "";',"\n";
print '        posgt = str.indexOf(">", poslt);',"\n";
print '     }',"\n";
print '    while(true) {',"\n";
print '        if((poslt = str.indexOf("<", posgt)) == -1) {',"\n";
print '            result += str.substring(posgt + 1, str.length);',"\n";
print '            break;',"\n";
print '        }',"\n";
print '        result += str.substring(posgt + 1, poslt);',"\n";
print '        if((posgt = str.indexOf(">", poslt)) == -1)',"\n";
print '            break;',"\n";
print '    }',"\n";
print '    return result;',"\n";
print '}',"\n";
print '',"\n";

print 'function strRep(msg,key,rep){',"\n";
print 'var n=0;',"\n";
print '        while ((n=msg.indexOf(key,n))!=-1){',"\n";
print '        msg=msg.substring(0,n)+rep+msg.substring(n+key.length,msg.length);',"\n";
print '        n=n+rep.length;',"\n";
print '        }',"\n";
print '        return msg;',"\n";
print '}',"\n";
print '',"\n";

print 'var br;',"\n";
print 'var navi = navigator.userAgent;',"\n";
print '        if(navi.indexOf("Win") != -1) br = "\r\n";',"\n";
print '        else if(navi.indexOf("Mac") != -1) br = "\r";',"\n";
print '        else br = "\n";',"\n";

print 'function R(u,b){',"\n";
print '    b = strRep(b,"<BR>","__BR__");',"\n";
#print '    b = removetags(b);',"\n";
print '    b = document.inForm.comment.value+u+br+"> "+b;',"\n";
print '    restxt = strRep(b,"__BR__",br+"> ")+br;',"\n";
print '    document.inForm.comment.value = restxt;',"\n";
print '}',"\n";
print '',"\n";

print 'function MyFace(Smile) {',"\n";
print 'myComment = document.inForm.comment.value;',"\n";
print 'document.inForm.comment.value = myComment + Smile;',"\n";
print '}',"\n";
print '',"\n";

print '//-->',"\n";

print '</SCRIPT>',"\n";


print "</HEAD>\n\n";
print '<BODY LINK="#191970" ALINK="#FF0000" VLINK="#808080" BGCOLOR="#EFEFEF">',"\n\n";
#print '<BASE TARGET="colla">',"\n\n";
print '<A HREF="collaborate/manual/index.html"><IMG SRC="gif/panic.gif" BORDER=0></A><BR>',"\n\n";

# 初めの部分を書く
#
$val = <<"EOF";
<FONT SIZE=1 COLOR="#CCCCCC">FUJIXEROX INTERNAL USE ONLY, 作成責任者： 秋山浩一 作成年月日： リアルタイム</FONT>

<BR>
<TABLE BORDER="0" WIDTH="100%"><TR><TD>

<A HREF="check.cgi">本日</A>/
<A HREF="$HREF_HOME/chat.log.0.html" TARGET="chat.log">日</A>/
<A HREF="$HREF_HOME/chat.log.1.html" TARGET="chat.log">月</A>/
<A HREF="$HREF_HOME/chat.log.2.html" TARGET="chat.log">火</A>/
<A HREF="$HREF_HOME/chat.log.3.html" TARGET="chat.log">水</A>/
<A HREF="$HREF_HOME/chat.log.4.html" TARGET="chat.log">木</A>/
<A HREF="$HREF_HOME/chat.log.5.html" TARGET="chat.log">金</A>/
<A HREF="$HREF_HOME/chat.log.6.html" TARGET="chat.log">土</A>/
<A HREF="$HREF_HOME/chat.man.html" TARGET="chat.man">Help</A>/
<A HREF="$HREF_HOME/GIF/kaomihon.html" TARGET="kaomihon">顔見本</A><BR>
</TD>
</TR></TABLE>
EOF

Jcode::convert(\$val, $kanji, $p_kanji);

if ($field{'quiet'} eq '1') {
    ;
}
else {
    print $val;
}

# FORM文
#
print '<FORM NAME="inForm" ACTION="',$ENV{'SCRIPT_NAME'},
    '?refresh=',$field{'refresh'},
    '&since=',$field{'since'},
    '&quiet=',$field{'quiet'},
    '" METHOD="POST"',"\n";

# 名前
#
$val = <<"EOF";
<UL>
<LI>名前(匿名時には「匿名」という文字を入れる)<BR>
EOF

Jcode::convert(\$val, $kanji, $p_kanji);
print $val;

Jcode::convert(\$field{'myname'}, $kanji, $p_kanji);
print '<INPUT TYPE="text" NAME="myname" VALUE="',
    $field{'myname'},'" SIZE="50">',"\n";
print '<INPUT TYPE="hidden" NAME="dupcheck" VALUE="',
    $now,'">',"\n";

# メッセージテキストエリア
#
$val = <<"EOF";
<SELECT name="feeling">
<OPTION value="general" selected>
<OPTION value="joyful">＼(^o^)／
<OPTION value="happy">(^_^)
<OPTION value="impatience">(^_^;)
<OPTION value="fear">(\@_\@;)
<OPTION value="cheers">( ^_^)／□☆□＼(^_^ )
<OPTION value="angry">凸(-_-)
<OPTION value="amazed">(-_-;)
<OPTION value="sad">(T_T)
<OPTION value="question">(・・？)
<OPTION value="joke">(*^_^*)
<OPTION value="memo">φ(・・)メモメモ
<OPTION value="serius">(・・)
<OPTION value="smoke">(-。-)y-。oO◯
<OPTION value="poripori">(^^ゞ
<OPTION value="maamaa">＼(^^;;)...マアマア
<OPTION value="hafuun">ヽ( ´ー)ノはふ〜ん
<OPTION value="smile">:-)
<OPTION value="cynical">;-)
<OPTION value="joke2">:-p
<OPTION value="uum">X-<
<OPTION value="uum2">:-<
<OPTION value="amazed2">:-O
<OPTION value="smile2">:->
<OPTION value="zipup">:-|
<OPTION value="glasses">B-|
<OPTION value="widehappy">:-D
<OPTION value="wakuwaku">o(^-^)o
<OPTION value="joyful2">(^O^)
<OPTION value="joyful3">(^o^)v
<OPTION value="joyful4">(^◇^)
<OPTION value="ouch">(>_<)
<OPTION value="surprised">(+_+)
<OPTION value="suspend">(／_・)／オイトイテ
<OPTION value="wink">(^_-)-☆
<OPTION value="question2">(?_?)
<OPTION value="sad2">(・_・)
<OPTION value="sad3">(;_;)
<OPTION value="sorry">m(_ _)m
<OPTION value="angry2">(-_-メ)
<OPTION value="sleep">(-_-)zzz...
<OPTION value="goodby">(^_^)/^^^
</SELECT>
<LI>メッセージ(コメントは&lt;!-- comment --&gt;。URLは自動的にリンク)
<a href="javascript:MyFace('(^^)')">(^^)</a>
<a href="javascript:MyFace('(^_^)')">(^_^)</a>
<a href="javascript:MyFace('(+_+)')">(+_+)</a>
<a href="javascript:MyFace('(^o^)')">(^o^)</a>
<a href="javascript:MyFace('(^^;)')">(^^;)</a>
<a href="javascript:MyFace('(^_-)')">(^_-)</a>
<a href="javascript:MyFace('(;_;)')">(;_;)</a>
<a href="javascript:MyFace('<FONT FACE=Symbol COLOR=red>ｩ<\/FONT>')"><FONT FACE=Symbol>ｩ<\/FONT></a>
<a href="javascript:MyFace('<a href=&quot;&quot; target=&quot;_blank&quot;></a>')">LINK</a>

<BR>
<TEXTAREA NAME="comment" ROWS=5 COLS=78 WRAP="soft">$kakikake</TEXTAREA>
<LI>リフレッシュ間隔：
<SELECT name="refresh">
EOF

Jcode::convert(\$val, $kanji, $p_kanji);
print $val;

# リフレッシュ間隔
#
@refresh = ("30", "60", "180", "300", "600", "3600", "10800", "28800", "86400", "never");

foreach (@refresh) {
  print '<OPTION value="',$_,'"';
  if ($_ eq $field{'refresh'}) {
      print ' selected';
  }
  print '>',$_,"\n";
}

# メンバー表示
#
$val = "</SELECT>秒\n　　メンバー表示：\n";
Jcode::convert(\$val, $kanji, $p_kanji);
print $val;
print '<SELECT name="since">',"\n";
@since = ("0.25", "0.5", "1", "2", "3", "8", "24", "240", "1e20", "never");
foreach (@since) {
  print '<OPTION value="',$_,'"';
  if ($_ eq $field{'since'}) {
      print ' selected';
  }
  print '>',$_,"\n";
}

$val = <<"EOF";
</SELECT>時間以内　　
EOF

Jcode::convert(\$val, $kanji, $p_kanji);
print $val;

if ($field{'quiet'} eq '1') {
    print 'Quiet: <INPUT TYPE="checkbox" CHECKED NAME="quiet" VALUE="1"><BR>';
}
else {
    print 'Quiet: <INPUT TYPE="checkbox" NAME="quiet" VALUE="1"><BR>';
}

# 引用の作成
#
$loop = 0;
while ($loop < $QUOTE_TIMES) {
    open (IN, "$LAST_MSG_FILE.$loop");
    $last_user[$loop] = '';
    $last_msg[$loop] = '';
    $msg_count = 0;
    while (<IN>) {
	chomp;
	if ($msg_count == 0) {
	    s/\<IMG/\<III/gmoi;
	    $last_user[$loop] = $_;
	    $msg_count++;
	}
	else {
	    $last_msg[$loop] = $last_msg[$loop].$_;
	}
    }
    close (IN);
    $last_user[$loop] =~ s/<BR>$//;
    $last_user[$loop] =~ s/'/\\'/;
    $last_user[$loop] =~ s/"/\\"/;
    $last_msg[$loop] =~ s/<BR>$//;
    $last_msg[$loop] =~ s/'/\\'/;
    $last_msg[$loop] =~ s/"/\\"/;

    # タグを削除する
    $text_regex = q{[^<]*};
    $tag_regex_ = q{[^"'<>]*(?:"[^"]*"[^"'<>]*|'[^']*'[^"'<>]*)*(?:>|(?=<)|$(?!\n))}; #'}}}}
    $comment_tag_regex =
	'<!(?:--[^-]*-(?:[^-]+-)*?-(?:[^>-]*(?:-[^>-]+)*?)??)*(?:>|$(?!\n)|--.*$)';
    $tag_regex = qq{$comment_tag_regex|<$tag_regex_};

    $result = '';
    $str = $last_msg[$loop];
    Jcode::convert(\$str, $p_kanji, $kanji);

    while ($str =~ /($text_regex)($tag_regex)?/gso) {
	last if $1 eq '' and $2 eq '';
	$result .= $1;
	$tag_tmp = $2;
	$result .= $tag_tmp if $tag_tmp =~ /^<\/?(BR)(?![0-9A-Za-z])/i;
	if ($tag_tmp =~ /^<(XMP|PLAINTEXT|SCRIPT)(?![0-9A-Za-z])/i) {
	    $str =~ /(.*?)(?:<\/$1(?![0-9A-Za-z])$tag_regex_|$)/gsi;
			   ($text_tmp = $1) =~ s/</&lt;/g;
			   $text_tmp =~ s/>/&gt;/g;
			   $text_tmp =~ s/'/\'/g;
			   $result .= $text_tmp;
	}
    }
    Jcode::convert(\$result, $kanji, $p_kanji);
    $last_msg[$loop] = $result;

    $ref_count[$loop] = $last_user[$loop];
    $ref_count[$loop] =~ s/([0-9]+)/$1/;
    $ref_count[$loop] = $1;

    $loop++;
}


$val = <<"EOF";
</UL>
<A HREF="check.cgi"><!IMG SRC="nph-nextcheck.cgi" BORDER=0 WIDTH=40 HEIGHT=37></A>
<INPUT TYPE="submit" NAME="option" VALUE="書き込む">
<INPUT TYPE="reset">
引用
EOF

$loop = 0;
while ($loop < $QUOTE_TIMES) {
    $val = $val
    . qq#<INPUT type="radio" name="rd" onClick="R(lastuser$loop, lastmsg$loop)"> $ref_count[$loop]\n#;

    $loop++;
}

$val = $val.'<INPUT TYPE="submit" NAME="option" VALUE="再表示">'
    ."</FORM>\n".qq#<HR SIZE="1" NOSHADE>\n#;

Jcode::convert(\$val, $kanji, $p_kanji);
print $val;



print '<SCRIPT language="JavaScript">',"\n";
print '<!--',"\n";

$loop = 0;
while ($loop < $QUOTE_TIMES) {
    print "var lastuser$loop=","'",$last_user[$loop],"';\n";
    print "var lastmsg$loop=","'",$last_msg[$loop],"'",";\n";

    $loop++;
}

print '//-->',"\n";
print '</SCRIPT>',"\n";

if ($field{'quiet' eq '1'}) {
    print '<INPUT TYPE="checkbox" CHECKED NAME="quiet" VALUE="1">';
}
else {
    print '<INPUT TYPE="checkbox" NAME="quiet" VALUE="1">';
}


print '<TABLE CELLPADDING="1" BGCOLOR="#F3F3F3" BORDER="1">',"\n";
print '<CAPTION ALIGN="top">';

printf  "<STRONG>";
print  $date;
printf  "%2.2d:%2.2d:%2.2d", $hour, $min, $sec ;

$val = "　：　$sort_uniq名";
Jcode::convert(\$val, $kanji, $p_kanji);
print $val;

print "</STRONG><BR>\n";
print '</CAPTION>';
print '<TR>',"\n";

foreach (@sort_uniq) {
  if (/\S/o) {
      print '<TD ALIGN="center" VALIGN="top">',"\n";
      s/\<IMG/\<III/gmoi;
      Jcode::convert(\$_, $kanji, $p_kanji);
      print $_;
      print '</TD>',"\n";
  }
}

print '</TR>',"\n";
print '</TABLE>',"\n";

#print '<P><HR SIZE="10" COLOR="#ffdab9"><BR>',"\n";
print '<A HREF="collaborate/manual/index.html"><IMG SRC="gif/panic.gif" BORDER=0></A><BR>',"\n";

    if ($field{'quiet'} eq '1') {
	file_print2 (*STDOUT, "$BODY_FILE");
    }
    else {
	file_print (*STDOUT, "$BODY_FILE");
    }

$val = <<"EOF";
</TABLE>
EOF

Jcode::convert(\$val, $kanji, $p_kanji);
print $val;

print '</BODY>',"\n";
print '</HTML>',"\n";
