<?php

function booleanReduce($a, $b)
{
    return $a && $b;
}

/**
 * Check to see if Airtime is properly configured.
 *
 * @return bool true if all Airtime dependencies and services are
 *              properly configured and running
 */
function checkConfiguration()
{
    $r1 = array_reduce(checkPhpDependencies(), 'booleanReduce', true);
    $r2 = array_reduce(checkExternalServices(), 'booleanReduce', true);

    return $r1 && $r2;
}

/**
 * Check for Airtime's PHP dependencies and return an associative
 * array with the results.
 *
 * @return array associative array of dependency check results
 */
function checkPhpDependencies()
{
    return [
        'postgres' => checkDatabaseDependencies(),
    ];
}

/**
 * Check that the PHP dependencies for the database exist.
 *
 * @return bool true if the database dependencies exist
 */
function checkDatabaseDependencies()
{
    global $extensions;
    // Check the PHP extension list for the Postgres db extensions
    return in_array('pdo_pgsql', $extensions)
        && in_array('pgsql', $extensions);
}

/**
 * Check that all external services are configured correctly and return an associative
 * array with the results.
 *
 * @return array associative array of external service check results
 */
function checkExternalServices()
{
    return [
        'database' => checkDatabaseConfiguration(),
        'analyzer' => checkAnalyzerService(),
        'pypo' => checkPlayoutService(),
        'liquidsoap' => checkLiquidsoapService(),
        'rabbitmq' => checkRMQConnection(),
        'celery' => checkCeleryService(),
        'api' => checkApiService(),
    ];
}

/**
 * Check the database configuration by fetching a connection from Propel.
 *
 * @return bool true if a connection is made to the database
 */
function checkDatabaseConfiguration()
{
    configureDatabase();

    try {
        // Try to establish a database connection. If something goes
        // wrong, the database is improperly configured
        Propel::getConnection();
        Propel::close();
    } catch (Exception $e) {
        return false;
    }

    return true;
}

/**
 * Initialize Propel to configure the Airtime database.
 */
function configureDatabase()
{
    Propel::init(PROPEL_CONFIG_FILEPATH);
}

/**
 * Check that we can connect to RabbitMQ.
 *
 * @return true if the RabbitMQ connection can be established
 */
function checkRMQConnection()
{
    $config = Config::getConfig();

    $conn = new \PhpAmqpLib\Connection\AMQPStreamConnection(
        $config['rabbitmq']['host'],
        $config['rabbitmq']['port'],
        $config['rabbitmq']['user'],
        $config['rabbitmq']['password'],
        $config['rabbitmq']['vhost']
    );

    return isset($conn);
}

/**
 * Check if airtime-analyzer is currently running.
 *
 * @return bool true if airtime-analyzer is running
 */
function checkAnalyzerService()
{
    exec('systemctl is-active libretime-analyzer --quiet', $out, $status);

    return $status == 0;
}

/**
 * Check if libretime-playout is currently running.
 *
 * @return bool true if libretime-playout is running
 */
function checkPlayoutService()
{
    exec('systemctl is-active libretime-playout --quiet', $out, $status);

    return $status == 0;
}

/**
 * Check if libretime-liquidsoap is currently running.
 *
 * @return bool true if libretime-liquidsoap is running
 */
function checkLiquidsoapService()
{
    exec('systemctl is-active libretime-liquidsoap --quiet', $out, $status);

    return $status == 0;
}

/**
 * Check if libretime-celery is currently running.
 *
 * @return bool true if libretime-celery is running
 */
function checkCeleryService()
{
    exec('systemctl is-active libretime-celery --quiet', $out, $status);

    return $status == 0;
}

/**
 * Check if libretime-api is currently running.
 *
 * @return bool true if libretime-api is running
 */
function checkApiService()
{
    exec('systemctl status libretime-api --quiet', $out, $status);

    return $status == 0;
}
