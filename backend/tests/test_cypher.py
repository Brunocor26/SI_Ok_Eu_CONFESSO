def test_cypher_and_decypher():
    #some plaintext
    msg = "Hello world"
    key = get_key("somekey1364")

    #cypher
    cyphertext = cypher(msg, key)

    #check if it really cyphered it
    assert msg!=cyphertext
    #check if when we decypher it is correct (assume its symmetric)
    assert msg == decypher(cyphertext, key)