-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 12-06-2024 a las 23:03:58
-- Versión del servidor: 10.4.27-MariaDB
-- Versión de PHP: 8.2.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `bd_importarexcel`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `establecimiento`
--

CREATE TABLE `establecimiento` (
  `idEstablecimiento` int(11) NOT NULL,
  `descripcionEsta` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_spanish_ci;

--
-- Volcado de datos para la tabla `establecimiento`
--

INSERT INTO `establecimiento` (`idEstablecimiento`, `descripcionEsta`) VALUES
(1, 'P.S HUAHUARI'),
(2, 'C.S RIO NEGRO'),
(3, 'P.S VILLA CAPIRI'),
(4, 'P.S RIO CHARI ALTO'),
(5, 'P.S PITOCUNA'),
(6, 'P.S PUENTE IPOKI'),
(7, 'P.S ALTO PITOCUNA'),
(8, 'P.S CUSHIVIANI'),
(9, 'P.S UNION CUBIRIAKI'),
(10, 'P.S SHABASHIPANGO'),
(11, 'P.S SAN JUA CHENI'),
(12, 'P.S UNION CAPIRI'),
(13, 'P.S MIGUEL GRAU'),
(14, 'P.S ALTO VILLA VICTORIA');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `madre`
--

CREATE TABLE `madre` (
  `dniMadre` varchar(20) NOT NULL,
  `nombresMadre` varchar(25) NOT NULL,
  `apellidoPaterno_Madre` varchar(25) NOT NULL,
  `apellidomaterno_Madre` varchar(25) NOT NULL,
  `celularMadre` varchar(15) NOT NULL,
  `idMenor` varchar(25) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `niños`
--

CREATE TABLE `niños` (
  `num` int(11) NOT NULL,
  `tipoDocumento` varchar(25) CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci NOT NULL,
  `nombres` varchar(20) NOT NULL,
  `apellidoPaterno` varchar(20) NOT NULL,
  `apellidoMaterno` varchar(20) NOT NULL,
  `fechaNacimiento` varchar(30) NOT NULL,
  `sexo` int(11) NOT NULL,
  `programa` varchar(20) NOT NULL,
  `idEstablecimiento` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_spanish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `padre`
--

CREATE TABLE `padre` (
  `dniPadre` varchar(20) NOT NULL,
  `nombresPadre` varchar(25) NOT NULL,
  `apellidoPaterno_Padre` varchar(25) NOT NULL,
  `apellidoMaterno_Padre` varchar(25) NOT NULL,
  `idMenor` varchar(25) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `reportehemoglobina`
--

CREATE TABLE `reportehemoglobina` (
  `idReporteHG` bigint(20) DEFAULT NULL,
  `idMenor` varchar(25) DEFAULT NULL,
  `grupoEdad` varchar(30) DEFAULT NULL,
  `HG1` varchar(30) DEFAULT NULL,
  `fecha1` varchar(30) DEFAULT NULL,
  `HG2` varchar(30) DEFAULT NULL,
  `fecha2` varchar(30) DEFAULT NULL,
  `HG3` varchar(30) DEFAULT NULL,
  `fecha3` varchar(30) DEFAULT NULL,
  `fecha4` varchar(30) DEFAULT NULL,
  `HG4` varchar(30) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `sexo`
--

CREATE TABLE `sexo` (
  `idSexo` int(11) NOT NULL,
  `descripcionSexo` varchar(15) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_spanish_ci;

--
-- Volcado de datos para la tabla `sexo`
--

INSERT INTO `sexo` (`idSexo`, `descripcionSexo`) VALUES
(1, 'MASCULINO'),
(2, 'FEMENINO');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `idUsuario` int(11) NOT NULL,
  `nombres` varchar(20) NOT NULL,
  `usuario` varchar(20) NOT NULL,
  `password` varchar(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`idUsuario`, `nombres`, `usuario`, `password`) VALUES
(1, 'WILLY ALCALA', 'admin', 'willy123'),
(2, 'MIGUEL GOZME', 'admin2', 'miguel123');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `establecimiento`
--
ALTER TABLE `establecimiento`
  ADD PRIMARY KEY (`idEstablecimiento`);

--
-- Indices de la tabla `niños`
--
ALTER TABLE `niños`
  ADD PRIMARY KEY (`tipoDocumento`),
  ADD KEY `fk_sexo_niño` (`sexo`),
  ADD KEY `fk_niño_establecimiento` (`idEstablecimiento`);

--
-- Indices de la tabla `reportehemoglobina`
--
ALTER TABLE `reportehemoglobina`
  ADD KEY `fk_report_hg` (`idMenor`);

--
-- Indices de la tabla `sexo`
--
ALTER TABLE `sexo`
  ADD PRIMARY KEY (`idSexo`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`idUsuario`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `establecimiento`
--
ALTER TABLE `establecimiento`
  MODIFY `idEstablecimiento` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `sexo`
--
ALTER TABLE `sexo`
  MODIFY `idSexo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `idUsuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `niños`
--
ALTER TABLE `niños`
  ADD CONSTRAINT `fk_niño_establecimiento` FOREIGN KEY (`idEstablecimiento`) REFERENCES `establecimiento` (`idEstablecimiento`),
  ADD CONSTRAINT `fk_sexo_niño` FOREIGN KEY (`sexo`) REFERENCES `sexo` (`idSexo`);

--
-- Filtros para la tabla `reportehemoglobina`
--
ALTER TABLE `reportehemoglobina`
  ADD CONSTRAINT `fk_report_hg` FOREIGN KEY (`idMenor`) REFERENCES `niños` (`tipoDocumento`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
