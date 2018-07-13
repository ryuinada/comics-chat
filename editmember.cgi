#!/usr/local/bin/perl

# Member Editor v1.0 "editmember.cgi" is Freeware.
# for NCSA,Apache on UNIX
# by www.rescue.ne.jp
#
# [History]
# 27/OCT/98 v1.0 初期版リリース

#---------------------------------------------------------------------
#■パスワードファイル編集用管理者パスワード "ADMIN_KEY"
#　このＣＧＩを実行した際に入力が必要な編集者用のパスワードの設定です。
#　添付のパスワード生成ツールcrypt.cgiで生成した暗号化されたパスワードをそのままコピーします。
#　$admin_key = 'この部分にコピーします';

$admin_key = 'hgQ/YM0ok0cMY';
#---------------------------------------------------------------------

#○使い方
#　既にパスワードファイルの仕様などを理解している必要があります。
#　http://www.rescue.ne.jp/cgi-rescue/cgi?htpasswd
#　ＣＧＩを実行すると編集するパスワードファイル名(FILENAME)と管理者パスワード(ADMIN_KEY)を
#　入力します。パスワードファイルは同じサーバ内であればどこにあっても構いません。
#　このＣＧＩと異なる場所にある場合は、絶対パスまたは相対パスで指定します。
#　編集するパスワードファイルは書き換え可能状態になっている必要がありますので、
#　パーミッションは666(環境に応じて606や600に)に設定しておく必要があります。
#
#　ファイルの内容を直接編集してコメント追加やＩＤ(username)の変更、削除などが可能です。
#　行頭に#を置くことでコメント行となります。Undoボタンで前回の編集内容に戻ります。
#　ＩＤの重複はできないので、そのチェック機能があります。

#○注意事項
#　書き換え実行が重複してしまうとトラブルが起き、ファイルが破損する可能性があります。
#　実行ボタンは必ず１回だけ押して処理をお待ちください。サーバの混雑などで反応が来ない
#　場合はストップして、ＦＴＰ等からファイルの状態を確認してください。また、実行毎に
#　編集画面をコピーしたものをパソコン上のファイルにバックアップとして保存してください。

#○エラーメッセージの解説
#　Authorization Required　管理者パスワードが合致しません
#　File Not Found　編集するファイルが見つかりません
#　Read Error　編集するファイルを読み込めません
#　Bad Username　ユーザ名が重複しています
#　Bad Chr. _,A-Z,a-z and 0-9　使えない文字の入力があります
#　Bad Length 4-12　パスワードは4から12文字で入力してください
#　Forbidden　編集するファイルに上書きできません

$QUERY_STRING = $ENV{'QUERY_STRING'};
if ($QUERY_STRING eq '') { &input; }
if ($QUERY_STRING =~ /^action$/i) { &check; &edit; }
elsif ($QUERY_STRING =~ /^regist$/i) { &check; &regist; &edit; }
else { &input; }

sub check {

read(STDIN,$buffer,$ENV{'CONTENT_LENGTH'});
@pairs = split(/&/,$buffer);
@pairs = (grep(/^action=/,@pairs),grep(!/^action=/,@pairs));
foreach $pair (@pairs) {

	($name, $value) = split(/=/, $pair);
	$value =~ tr/+/ /;
	$value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
	$value =~ s/\r\n/\n/g;
	$value =~ s/\r/\n/g;
	if ($name eq 'TEXTAREA') { push(@new,$value); }
	else { $FORM{$name} = $value; }
}
system ("cp $FORM{'FILENAME'} $FORM{'FILENAME'}.bak");

if ($FORM{'FILENAME'} eq '') { &input; }
if ($admin_key =~ /^\$1\$/) { $salt = 3; } else { $salt = 0; }
if (crypt($FORM{'ADMIN_KEY'},substr($admin_key,$salt,2)) ne $admin_key) { &error('Authorization Required',''); }
if (!-e $FORM{'FILENAME'}) { &error('File Not Found',''); }
if ($buffer eq '' || $FORM{'ADMIN_KEY'} eq '') { &error('Error',''); }
}

sub edit {

if (!open(DB,"$FORM{'FILENAME'}")) { &error('Read Error',''); }

print "Content-type: text/html\n\n";
print <<"EOF";
<html><head>
<meta http-equiv="content-type" content="text/html; charset=EUC-JP">
<title>Member Editor</title></head>
<body>
<h3>$FORM{'FILENAME'}</h3>
<form method=POST action="editmember.cgi?regist">
<input type=hidden name="FILENAME" value="$FORM{'FILENAME'}">
<input type=hidden name="ADMIN_KEY" value="$FORM{'ADMIN_KEY'}">
<textarea name="TEXTAREA" cols=100 rows=20 wrap="soft">
EOF

while (<DB>) {

	s/&/&amp;/g;
	s/</&lt;/g;
	s/>/&gt;/g;
	s/"/&quot;/g;
	print;
}
close(DB);

print <<"EOF";
</textarea><br>
<input type=submit value="Submit"><input type=reset value="Reset">
</form>
EOF

if ($QUERY_STRING ne 'action') {

print <<"EOF";
<form method=POST action="editmember.cgi?regist">
<input type=hidden name="FILENAME" value="$FORM{'FILENAME'}">
<input type=hidden name="ADMIN_KEY" value="$FORM{'ADMIN_KEY'}">
EOF

print '<input type=hidden name="TEXTAREA" value="';

foreach (@undo) {

	s/&/&amp;/g;
	s/</&lt;/g;
	s/>/&gt;/g;
	s/"/&quot;/g;
	print;
}

print <<"EOF";
">
<input type=submit value="Undo">
</form>
EOF
}

print <<"EOF";
</body>
</html>
EOF
exit;

}

sub regist {

if (!open(DB,"$FORM{'FILENAME'}")) { &error('Read Error',''); }
@undo = <DB>;
close(DB);

if (!open(DB,"> $FORM{'FILENAME'}")) { &error('Forbidden',''); }
print DB @new;
close(DB);
}

sub input {

print "Content-type: text/html\n\n";
print <<"EOF";
<html><head>
<meta http-equiv="content-type" content="text/html; charset=EUC-JP">
<title>Member Editor</title></head>
<!-- Member Editor v1.0 by www.rescue.ne.jp -->
<body>
<h3>Member Editor</h3>
<form method=POST action="editmember.cgi?action">
<input type=hidden name="FILENAME" value="/home/akiyama/public_html/collaborate/member/members" size=40><br>
Password <input type=password name="ADMIN_KEY" value="" size=10><p>
<br>
<input type=submit value="Submit">
</form>
</body>
</html>
EOF
exit;

}

sub error {

print "Content-type: text/html\n\n";
print <<"EOF";
<html><head><title>Member Editor</title></head>
<body>
<h1>$_[0]</h1>
<h3>$_[1]</h3>
</body>
</html>
EOF
exit;

}
