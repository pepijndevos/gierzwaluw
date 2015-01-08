<?php
ini_set('display_errors',1);
ini_set('display_startup_errors',1);
error_reporting(-1);

$pdo = new PDO("mysql:host=localhost;dbname=foo", 'bar', 'baz');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$pdo->exec("CREATE TABLE IF NOT EXISTS mappings (
           id INT(32) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
           privip VARBINARY(16),
           pubip VARBINARY(16),
           hostname VARCHAR(128),
	   age TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
           UNIQUE INDEX idx_pubip (pubip, privip))");

$addipstmt = $pdo->prepare("INSERT INTO mappings
                           (pubip, privip, hostname) VALUES
                           (INET_ATON(:pubip), INET_ATON(:privip), :hostname)
                           ON DUPLICATE KEY UPDATE
                           hostname = :hostname,
                           age = NOW()");

$getipstmt = $pdo->prepare("SELECT INET_NTOA(privip) as ip, hostname FROM mappings
                             WHERE pubip = INET_ATON(:pubip)
                               AND age > DATE_SUB(now(), INTERVAL 5 MINUTE)");

function add_ip($privip, $hostname) {
	global $addipstmt;
	$addipstmt->bindParam(':pubip', $_SERVER['REMOTE_ADDR']);
	$addipstmt->bindParam(':privip', $privip);
	$addipstmt->bindParam(':hostname', $hostname);
	$addipstmt->execute();
}

function list_local() {
	global $getipstmt;
	$getipstmt->bindParam(':pubip', $_SERVER['REMOTE_ADDR']);
	$getipstmt->execute();
	return $getipstmt->fetchAll(PDO::FETCH_ASSOC);
}

if (isset($_GET['ip']) && isset($_GET['hostname'])) {
	add_ip($_GET['ip'], $_GET['hostname']);
}

?>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Local file sharing nodes</title>

    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css">

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>

  <body>

    <div class="container">

      <div class="starter-template">
        <h1>Local file sharing nodes</h1>

<ul class="list-unstyled">
<?php
foreach (list_local() as $row) {
?>
<li class="well"><a href="http://<?php echo $row['ip']; ?>:7557"><?php echo $row['hostname']; ?></a></li>
<?php
}
?>
</ul>
      </div>

    </div><!-- /.container -->

  </body>
</html>
