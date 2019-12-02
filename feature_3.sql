-- set default value of postingdate
ALTER TABLE Photo 
MODIFY COLUMN postingdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
