-- ============================================================
-- 1. Adiciona coluna IS_ADMIN na tabela USUARIO
--    Firebird 2.5 usa SMALLINT para booleano (0 = não, 1 = sim)
--    DEFAULT 0 = não admin
-- ============================================================
ALTER TABLE USUARIO
  ADD IS_ADMIN SMALLINT DEFAULT 0 NOT NULL;


-- ============================================================
-- 2. Promover um usuário a admin pelo username
--    Substitua 'nome_do_usuario' pelo username desejado
-- ============================================================
UPDATE USUARIO
  SET IS_ADMIN = 1
  WHERE USERNAME = 'nome_do_usuario';
