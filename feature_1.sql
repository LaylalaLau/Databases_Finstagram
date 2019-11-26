SELECT photoID, photoPoster
FROM Photo
WHERE (allFollowers = True AND photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = "TestUser")) OR
(allFollowers = False AND photoID IN (
    SELECT photoID
    FROM SharedWith
    WHERE (groupName,groupOwner) IN(
    SELECT groupName,owner_username FROM BelongTo WHERE member_username = "TestUser")
)
)
ORDER BY postingdate DESC
