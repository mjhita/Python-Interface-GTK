-- 
--

DROP DATABASE IF EXISTS DBManuel;
CREATE DATABASE DBManuel;
GRANT ALL ON DBManuel.* TO 'manuel'@'localhost' IDENTIFIED BY 'hita';
USE DBManuel;
--
DROP TABLE IF EXISTS Amigos;

CREATE TABLE Amigos (
    Amigo_no    INT        , 
    Nombre      VARCHAR(40), 
    Procedencia VARCHAR(40), 
    EnComun     VARCHAR(40), 
    Telefono    VARCHAR(20), 
    Email       VARCHAR(40)
);
 
