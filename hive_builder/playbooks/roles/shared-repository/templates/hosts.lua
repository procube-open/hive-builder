-- https://github.com/hhoffstaette/dnsdist-utils/blob/master/hosts.lua より関数を引用
-- check whether a file exists and can be opened for reading
local function file_exists(name)
  local f = io.open(name, "r")
  return f ~= nil and io.close(f)
end

-- read all lines from given file & invoke callback with (ip, hostname) as argument;
-- nonexisting files are ignored.
local function forEachHost(file, callback)
  if not file_exists(file) then return end
  for line in io.lines(file) do
    -- ignore empty lines and comments
    if string.len(line) ~= 0 and string.find(line, "^#") == nil then
      -- ignore any localhost entries
      if not string.match(line, "localhost") then
        -- separate IP and all names
        for ip, space, host in string.gmatch(line, "(%g+)(%s+)(%g.+)") do
          -- create entries for every name
          for name in string.gmatch(host, "(%g+)") do
            callback(ip, name)
          end
        end
      end
    end
  end
end

function reverse_ip(ip_address)
  local octets = {}
  for octet in string.gmatch(ip_address, "%d+") do
    table.insert(octets, octet)
  end
  local reversed_octets = {}
  for i = #octets, 1, -1 do
    table.insert(reversed_octets, octets[i])
  end
  local reversed_ip = table.concat(reversed_octets, ".") .. ".in-addr.arpa."

  return reversed_ip
end

function convert_to_raw(hostname)
  local labels = {}
  local raw_str = ""
  for str in hostname:gmatch("([^.]+)") do
    table.insert(labels, str)
  end
  for i, label in ipairs(labels) do
    raw_str = raw_str .. string.char(label:len()) .. label
  end
  raw_str = raw_str .. "\000"
  return raw_str
end

-- create spoof rules for all entries in the given hosts file
function addHosts(file)
  local rules = {}
  forEachHost(file, function(ip, hostname)
    -- 正引き
    local forward_dns_rule = AndRule({QNameRule(hostname), QTypeRule(DNSQType.A)})
    addAction(forward_dns_rule, SpoofAction({ip}))
    table.insert(rules, forward_dns_rule)

    -- 逆引き
    local reverse_dns_rule = QNameRule(reverse_ip(ip))
    addAction(reverse_dns_rule, SpoofRawAction(convert_to_raw(hostname)))
    table.insert(rules, reverse_dns_rule)
  end)
  -- その他はresolv.confのDNSにプロキシ
  newServer({ address = '{{ lookup('file', '/etc/resolv.conf') | regex_findall('\\s*nameserver\\s*(.*)') | first}}', pool = 'external-dns' })
  addAction(NotRule(OrRule(rules)), PoolAction('external-dns'))
end

return {
  addHosts = addHosts
}
